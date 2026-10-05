// Windows process-tree loopback. PCM16 mono 24 kHz on stdout, diagnostics on stderr.
// Based on the documented ActivateAudioInterfaceAsync process-loopback API.
using System;
using System.IO;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Threading;

[ComImport, Guid("72A22D78-CDE4-431D-B8CC-843A71199B6D"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IActivationOperation {
    [PreserveSig] int GetActivateResult(out int result, [MarshalAs(UnmanagedType.IUnknown)] out object activated);
}
[Guid("41D949AB-9862-444A-80F6-C261334DA5EB"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ICompletionHandler {
    [PreserveSig] int ActivateCompleted(IActivationOperation operation);
}
[Guid("94EA2B94-E9CC-49E0-C0FF-EE64CA8F5B90"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IAgileObject { }
[ComVisible(true), ClassInterface(ClassInterfaceType.None)]
public class Completion : ICompletionHandler, IAgileObject {
    public ManualResetEvent Done = new ManualResetEvent(false);
    public object Activated;
    public int Result;
    public int ActivateCompleted(IActivationOperation operation) {
        try { int hr = operation.GetActivateResult(out Result, out Activated); if(hr < 0) Result = hr; }
        catch(Exception ex) { Result = Marshal.GetHRForException(ex); }
        finally { Done.Set(); }
        return 0;
    }
}
[StructLayout(LayoutKind.Sequential, Pack=2)]
public struct WaveFormat {
    public ushort Tag, Channels;
    public uint Rate, BytesPerSecond;
    public ushort BlockAlign, Bits, Extra;
}
[ComImport, Guid("1CB9AD4C-DBFA-4C32-B178-C2F568A703B2"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IAudioClient {
    [PreserveSig] int Initialize(int mode, uint flags, long duration, long periodicity, ref WaveFormat format, IntPtr session);
    [PreserveSig] int GetBufferSize(out uint frames);
    [PreserveSig] int GetStreamLatency(out long latency);
    [PreserveSig] int GetCurrentPadding(out uint padding);
    [PreserveSig] int IsFormatSupported(int mode, IntPtr format, out IntPtr closest);
    [PreserveSig] int GetMixFormat(out IntPtr format);
    [PreserveSig] int GetDevicePeriod(out long normal, out long minimum);
    [PreserveSig] int Start();
    [PreserveSig] int Stop();
    [PreserveSig] int Reset();
    [PreserveSig] int SetEventHandle(IntPtr handle);
    [PreserveSig] int GetService(ref Guid iid, [MarshalAs(UnmanagedType.IUnknown)] out object service);
}
[ComImport, Guid("C8ADBD64-E71E-48A0-A4DE-185C395CD317"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IAudioCaptureClient {
    [PreserveSig] int GetBuffer(out IntPtr data, out uint frames, out uint flags, out ulong position, out ulong qpc);
    [PreserveSig] int ReleaseBuffer(uint frames);
    [PreserveSig] int GetNextPacketSize(out uint frames);
}
public class ProcessAudio {
    [DllImport("Mmdevapi.dll", ExactSpelling=true, CharSet=CharSet.Unicode)]
    static extern int ActivateAudioInterfaceAsync(string path, ref Guid iid, IntPtr parameters,
        ICompletionHandler completion, out IActivationOperation operation);
    static void Check(int hr) { if(hr < 0) Marshal.ThrowExceptionForHR(hr); }
    static volatile bool stopping;
    [MTAThread]
    public static int Main(string[] args) {
        IAudioClient client = null;
        IAudioCaptureClient capture = null;
        IActivationOperation operation = null;
        Completion completion = new Completion();
        IntPtr parameters = IntPtr.Zero, blob = IntPtr.Zero;
        try {
            if(args.Length < 2) { Console.Error.WriteLine("Usage: ProcessAudio.exe PID SECONDS [PCM_FILE]; 0 seconds = until Ctrl+C"); return 2; }
            uint pid = uint.Parse(args[0]);
            double seconds = double.Parse(args[1], System.Globalization.CultureInfo.InvariantCulture);
            Process.GetProcessById((int)pid); // fail clearly for a stale PID
            Console.CancelKeyPress += delegate(object sender, ConsoleCancelEventArgs e) { stopping=true; e.Cancel=true; };
            // AUDIOCLIENT_ACTIVATION_PARAMS: PROCESS_LOOPBACK, pid, INCLUDE_TARGET_PROCESS_TREE.
            blob = Marshal.AllocHGlobal(12);
            Marshal.WriteInt32(blob,0,1); Marshal.WriteInt32(blob,4,(int)pid); Marshal.WriteInt32(blob,8,0);
            parameters = Marshal.AllocHGlobal(24);
            for(int i=0;i<24;i++) Marshal.WriteByte(parameters,i,0);
            Marshal.WriteInt16(parameters,0,65); // VT_BLOB
            Marshal.WriteInt32(parameters,8,12); Marshal.WriteIntPtr(parameters,16,blob);
            Guid iid = typeof(IAudioClient).GUID;
            Check(ActivateAudioInterfaceAsync("VAD\\Process_Loopback", ref iid, parameters, completion, out operation));
            if(!completion.Done.WaitOne(10000)) throw new TimeoutException("Audio activation timed out");
            Check(completion.Result);
            client=(IAudioClient)completion.Activated;
            WaveFormat format=new WaveFormat {Tag=1,Channels=1,Rate=24000,BytesPerSecond=48000,BlockAlign=2,Bits=16,Extra=0};
            using(AutoResetEvent ready=new AutoResetEvent(false)) {
                Check(client.Initialize(0,0x00020000u | 0x00040000u | 0x80000000u | 0x08000000u,0,0,ref format,IntPtr.Zero));
                Check(client.SetEventHandle(ready.SafeWaitHandle.DangerousGetHandle()));
                Guid captureId=typeof(IAudioCaptureClient).GUID;
                object service; Check(client.GetService(ref captureId,out service)); capture=(IAudioCaptureClient)service;
                using(Stream output=args.Length>2 ? (Stream)File.Create(args[2]) : Console.OpenStandardOutput()) {
                    Check(client.Start());
                    Console.Error.WriteLine("{\"event\":\"ready\",\"pid\":"+pid+",\"rate\":24000,\"channels\":1,\"bits\":16}");
                    Stopwatch clock=Stopwatch.StartNew(); long total=0,nonzero=0,discontinuities=0;
                    while(!stopping && (seconds<=0 || clock.Elapsed.TotalSeconds<seconds)) {
                        ready.WaitOne(100);
                        uint available; Check(capture.GetNextPacketSize(out available));
                        while(available>0) {
                            IntPtr data; uint count,flags; ulong pos,qpc;
                            Check(capture.GetBuffer(out data,out count,out flags,out pos,out qpc));
                            try {
                                byte[] bytes=new byte[checked((int)count*2)];
                                if((flags&2)==0) Marshal.Copy(data,bytes,0,bytes.Length);
                                for(int i=0;i<bytes.Length;i+=2) if(bytes[i]!=0 || bytes[i+1]!=0) nonzero++;
                                if((flags&1)!=0) discontinuities++;
                                output.Write(bytes,0,bytes.Length); output.Flush(); total+=count;
                            } finally { Check(capture.ReleaseBuffer(count)); }
                            Check(capture.GetNextPacketSize(out available));
                        }
                    }
                    Check(client.Stop());
                    Console.Error.WriteLine("{\"event\":\"done\",\"samples\":"+total+",\"nonzero_samples\":"+nonzero+",\"discontinuities\":"+discontinuities+"}");
                }
            }
            GC.KeepAlive(completion); return 0;
        } catch(Exception ex) { Console.Error.WriteLine("Capture failed: "+ex.Message+" (0x"+Marshal.GetHRForException(ex).ToString("X8")+")"); return 1; }
        finally {
            if(client!=null) { client.Stop(); Marshal.ReleaseComObject(client); }
            if(capture!=null) Marshal.ReleaseComObject(capture);
            if(operation!=null) Marshal.ReleaseComObject(operation);
            if(parameters!=IntPtr.Zero) Marshal.FreeHGlobal(parameters);
            if(blob!=IntPtr.Zero) Marshal.FreeHGlobal(blob);
        }
    }
}
