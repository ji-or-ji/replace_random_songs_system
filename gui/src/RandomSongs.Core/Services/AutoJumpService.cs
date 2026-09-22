using System.Diagnostics;

namespace RandomSongs.Core;

/// <summary>自动跳转：计算目标 URL 并交由系统浏览器打开。逻辑对齐 Python 版。</summary>
public static class AutoJumpService
{
    public static string ExpandUrl(string template, Song song)
    {
        if (string.IsNullOrEmpty(template))
        {
            return template;
        }
        var name = song?.SongName ?? "";
        var artist = song?.Artist ?? "";
        var query = $"{name} {artist}".Trim();
        return template
            .Replace("{query}", Uri.EscapeDataString(query))
            .Replace("{song}", Uri.EscapeDataString(name))
            .Replace("{artist}", Uri.EscapeDataString(artist));
    }

    /// <summary>按「自带链接优先 / 优先搜索 / 模式」算出要打开的地址；无需跳转时返回 null。</summary>
    public static string BuildUrl(Song song, AutoJumpSettings config)
    {
        if (song == null || config == null)
        {
            return null;
        }

        var songUrl = (song.Url ?? "").Trim();
        if (songUrl.Length > 0 && !config.PreferSearch)
        {
            return songUrl;
        }

        if (config.Mode == "search")
        {
            var query = $"{song.SongName} {song.Artist}".Trim();
            if (query.Length == 0)
            {
                return null;
            }
            return "https://search.bilibili.com/all?keyword=" + Uri.EscapeDataString(query);
        }

        if (config.Mode == "custom" && !string.IsNullOrWhiteSpace(config.CustomUrl))
        {
            return ExpandUrl(config.CustomUrl, song);
        }

        return null;
    }

    public static bool Open(string url)
    {
        if (string.IsNullOrWhiteSpace(url))
        {
            return false;
        }
        try
        {
            Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });
            return true;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[警告] 打开链接失败: {ex.Message}");
            return false;
        }
    }
}
