using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;
using System.Threading;

internal static class NativeHostLauncher
{
    private static int Main()
    {
        try
        {
            string executableDirectory = Path.GetDirectoryName(
                Assembly.GetExecutingAssembly().Location
            );
            string pythonPath = File.ReadAllText(
                Path.Combine(executableDirectory, "python-path.txt"),
                Encoding.UTF8
            ).Trim();

            if (!File.Exists(pythonPath))
            {
                Console.Error.WriteLine("Native host Python executable is missing: " + pythonPath);
                return 2;
            }

            ProcessStartInfo startInfo = new ProcessStartInfo
            {
                FileName = pythonPath,
                Arguments = "-m live_translate_subtitles.main",
                WorkingDirectory = Path.GetDirectoryName(pythonPath),
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardInput = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true
            };

            using (Process process = Process.Start(startInfo))
            {
                StartPump(
                    Console.OpenStandardInput(),
                    process.StandardInput.BaseStream,
                    true
                );
                Thread outputThread = StartPump(
                    process.StandardOutput.BaseStream,
                    Console.OpenStandardOutput(),
                    false
                );
                Thread errorThread = StartPump(
                    process.StandardError.BaseStream,
                    Console.OpenStandardError(),
                    false
                );

                process.WaitForExit();
                outputThread.Join();
                errorThread.Join();
                return process.ExitCode;
            }
        }
        catch (Exception error)
        {
            Console.Error.WriteLine("Native host launcher failed: " + error);
            return 1;
        }
    }

    private static Thread StartPump(Stream input, Stream output, bool closeOutput)
    {
        Thread thread = new Thread(delegate()
        {
            byte[] buffer = new byte[8192];
            try
            {
                int count;
                while ((count = input.Read(buffer, 0, buffer.Length)) > 0)
                {
                    output.Write(buffer, 0, count);
                    output.Flush();
                }
            }
            catch (IOException)
            {
                // Either side may close first during browser or host shutdown.
            }
            finally
            {
                if (closeOutput)
                {
                    output.Close();
                }
            }
        });
        thread.IsBackground = true;
        thread.Start();
        return thread;
    }
}
