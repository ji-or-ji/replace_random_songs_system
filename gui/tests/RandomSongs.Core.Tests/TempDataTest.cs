using RandomSongs.Core;

namespace RandomSongs.Core.Tests;

/// <summary>每个用例把数据根指向独立临时目录。</summary>
public abstract class TempDataTest : IDisposable
{
    protected TempDataTest()
    {
        TempDir = Path.Combine(Path.GetTempPath(), "rss_test_" + Guid.NewGuid().ToString("N"));
        AppPaths.DataRoot = TempDir;
        AppInitializer.Initialize(quiet: true);
    }

    protected string TempDir { get; }

    public void Dispose()
    {
        try
        {
            if (Directory.Exists(TempDir))
            {
                Directory.Delete(TempDir, recursive: true);
            }
        }
        catch
        {
            // 清理失败不影响结果
        }
    }
}
