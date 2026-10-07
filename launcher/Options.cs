using System;

namespace EbsLauncher
{
    // 명령줄 옵션. 학생은 옵션 없이 더블클릭, 테스트만 옵션을 쓴다.
    public sealed class Options
    {
        public int Port = 47815;
        public string Root;          // null이면 exe 옆 app\
        public bool OpenBrowser = true;
        public bool Quiet;           // 메시지 창 대신 종료 코드만

        public static Options Parse(string[] args)
        {
            var o = new Options();
            for (int i = 0; i < args.Length; i++)
            {
                switch (args[i])
                {
                    case "--port": o.Port = int.Parse(args[++i]); break;
                    case "--root": o.Root = args[++i]; break;
                    case "--no-browser": o.OpenBrowser = false; break;
                    case "--quiet": o.Quiet = true; break;
                }
            }
            return o;
        }
    }
}
