using System.Diagnostics;
using System.IO;

namespace RandomSongs.Core;

/// <summary>本地播放：歌曲带本地文件时，用系统默认播放器打开该文件。</summary>
public static class LocalPlaybackService
{
    public static bool HasLocalFile(Song song)
        => song != null && !string.IsNullOrWhiteSpace(song.LocalPath) && File.Exists(song.LocalPath);

    public static bool Play(Song song)
    {
        if (!HasLocalFile(song))
        {
            return false;
        }
        try
        {
            Process.Start(new ProcessStartInfo(song.LocalPath) { UseShellExecute = true });
            return true;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[警告] 播放本地文件失败: {ex.Message}");
            return false;
        }
    }
}
