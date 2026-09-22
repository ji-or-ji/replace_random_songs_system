using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace RandomSongs.Core;

/// <summary>QQ 音乐歌单拉取与同步。接口与 Python 版一致（c.y.qq.com 公开接口）。</summary>
public static class QqPlaylistService
{
    private const string Api = "https://c.y.qq.com/v8/fcg-bin/fcg_v8_playlist_cp.fcg";
    public const string ImportRequester = "QQ歌单导入";

    private static readonly HttpClient Http = CreateClient();

    private static HttpClient CreateClient()
    {
        var client = new HttpClient { Timeout = TimeSpan.FromSeconds(15) };
        client.DefaultRequestHeaders.UserAgent.ParseAdd(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36");
        client.DefaultRequestHeaders.Referrer = new Uri("https://y.qq.com/");
        return client;
    }

    /// <summary>从纯 ID 或形如 /playlist/123 的链接中提取歌单 ID；提不出返回 null。</summary>
    public static string ExtractPlaylistIdFromText(string text)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            return null;
        }
        var trimmed = text.Trim();
        if (trimmed.All(char.IsDigit))
        {
            return trimmed;
        }
        var match = Regex.Match(trimmed, @"/playlist/(\d+)");
        return match.Success ? match.Groups[1].Value : null;
    }

    /// <summary>解析歌单 ID：必要时跟随短链跳转。</summary>
    public static async Task<string> ResolvePlaylistIdAsync(string urlOrId)
    {
        var direct = ExtractPlaylistIdFromText(urlOrId);
        if (direct != null)
        {
            return direct;
        }

        var response = await Http.GetAsync(urlOrId.Trim()).ConfigureAwait(false);
        var finalUrl = response.RequestMessage?.RequestUri?.ToString() ?? "";
        var fromRedirect = ExtractPlaylistIdFromText(finalUrl);
        if (fromRedirect != null)
        {
            return fromRedirect;
        }
        throw new InvalidOperationException($"无法从链接中提取歌单 ID: {urlOrId}");
    }

    /// <summary>拉取歌单歌曲（返回未落盘的 Song，尚未分配 id）。</summary>
    public static async Task<List<Song>> FetchSongsAsync(string playlistId)
    {
        var query =
            "g_tk=5381&loginUin=0&hostUin=0&format=json&inCharset=utf8&outCharset=utf-8" +
            "&notice=0&platform=yqq.json&needNewCode=0&ct=24&cid=205360838&id=" + Uri.EscapeDataString(playlistId);

        var json = await Http.GetStringAsync($"{Api}?{query}").ConfigureAwait(false);
        using var doc = JsonDocument.Parse(json);
        var root = doc.RootElement;

        if (!root.TryGetProperty("code", out var code) || code.GetInt32() != 0)
        {
            var value = root.TryGetProperty("code", out var c) ? c.GetInt32() : -1;
            throw new InvalidOperationException($"QQ 接口返回错误: code={value}");
        }

        if (!root.TryGetProperty("data", out var data) ||
            !data.TryGetProperty("cdlist", out var cdlist) ||
            cdlist.ValueKind != JsonValueKind.Array ||
            cdlist.GetArrayLength() == 0)
        {
            throw new InvalidOperationException("歌单为空或不存在");
        }

        if (!cdlist[0].TryGetProperty("songlist", out var songlist) || songlist.ValueKind != JsonValueKind.Array)
        {
            return new List<Song>();
        }

        var songs = new List<Song>();
        foreach (var item in songlist.EnumerateArray())
        {
            var name = item.TryGetProperty("songname", out var n) ? n.GetString()?.Trim() : null;
            if (string.IsNullOrEmpty(name))
            {
                continue;
            }

            var artist = "";
            if (item.TryGetProperty("singer", out var singers) && singers.ValueKind == JsonValueKind.Array)
            {
                artist = string.Join(
                    "、",
                    singers.EnumerateArray()
                        .Select(s => s.TryGetProperty("name", out var sn) ? sn.GetString() : null)
                        .Where(x => !string.IsNullOrEmpty(x)));
            }

            var mid = item.TryGetProperty("songmid", out var m) ? m.GetString() : null;
            songs.Add(new Song
            {
                SongName = name,
                Artist = artist,
                Url = string.IsNullOrEmpty(mid) ? "" : $"https://y.qq.com/n/ryqq/songDetail/{mid}",
                RequestedBy = ImportRequester,
            });
        }
        return songs;
    }

    private static string DedupKey(Song song)
        => $"{(song.SongName ?? "").Trim().ToLowerInvariant()}\u0001{(song.Artist ?? "").Trim().ToLowerInvariant()}";

    /// <summary>
    /// 拉取 QQ 歌单并写入。<paramref name="targetPlaylistId"/> 为空时新建歌单（用 <paramref name="newPlaylistName"/>）。
    /// 返回 (歌单ID, 新增数量)。
    /// </summary>
    public static async Task<(string PlaylistId, int Added)> ImportAsync(
        string urlOrId,
        string newPlaylistName = null,
        string targetPlaylistId = null)
    {
        var qqId = await ResolvePlaylistIdAsync(urlOrId).ConfigureAwait(false);
        var fetched = await FetchSongsAsync(qqId).ConfigureAwait(false);
        if (fetched.Count == 0)
        {
            throw new InvalidOperationException("该歌单没有可用歌曲");
        }

        if (!string.IsNullOrEmpty(targetPlaylistId))
        {
            var songs = SongService.LoadSongs(targetPlaylistId);
            var existing = songs.Select(DedupKey).ToHashSet();
            var added = 0;
            foreach (var item in fetched)
            {
                if (!existing.Add(DedupKey(item)))
                {
                    continue;
                }
                songs.Add(SongService.Normalize(item));
                added++;
            }
            SongService.SaveSongs(targetPlaylistId, songs);
            return (targetPlaylistId, added);
        }

        var name = string.IsNullOrWhiteSpace(newPlaylistName) ? $"QQ歌单_{qqId}" : newPlaylistName!.Trim();
        var playlistId = PlaylistService.UniquePlaylistId(name);
        PlaylistService.RegisterPlaylist(playlistId, name, $"从 QQ 音乐歌单 {qqId} 导入");
        var normalized = fetched.Select(SongService.Normalize).ToList();
        PlaylistService.EnsurePlaylistFiles(playlistId, normalized);
        ConfigService.UpdateSongCount(playlistId, normalized.Count);
        return (playlistId, normalized.Count);
    }

    /// <summary>按配置把 QQ 歌单同步进目标歌单（默认当前歌单）。返回 (新增, 总数)。</summary>
    public static async Task<(int Added, int Total)> SyncAsync(string targetPlaylistId = null)
    {
        var config = ConfigService.Load();
        var qqId = config.QqSync?.PlaylistId?.Trim();
        if (string.IsNullOrEmpty(qqId))
        {
            throw new InvalidOperationException("尚未配置 QQ 歌单 ID");
        }

        var pid = string.IsNullOrEmpty(targetPlaylistId) ? ConfigService.GetCurrentPlaylistId() : targetPlaylistId;
        if (string.IsNullOrEmpty(pid))
        {
            throw new InvalidOperationException("没有可用的目标歌单");
        }

        var (_, added) = await ImportAsync(qqId, targetPlaylistId: pid).ConfigureAwait(false);
        var total = SongService.LoadSongs(pid).Count;
        HistoryService.RecordOperation("QQ歌单同步", $"QQ歌单: {qqId}, 新增: {added}首, 总计: {total}首", playlistId: pid);
        return (added, total);
    }

    /// <summary>启动时自动同步；任何失败都软着陆（离线/未配置时不抛）。返回状态文本或 null。</summary>
    public static async Task<string> AutoSyncOnStartAsync()
    {
        var config = ConfigService.Load();
        var sync = config.QqSync;
        if (sync == null || !sync.Enabled || !sync.AutoOnStart || string.IsNullOrWhiteSpace(sync.PlaylistId))
        {
            return null;
        }
        try
        {
            var (added, total) = await SyncAsync().ConfigureAwait(false);
            return $"QQ 歌单已同步：新增 {added} 首，共 {total} 首";
        }
        catch (Exception ex)
        {
            return $"QQ 自动同步失败（不影响使用）：{ex.Message}";
        }
    }
}
