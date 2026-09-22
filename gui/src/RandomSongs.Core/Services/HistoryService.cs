namespace RandomSongs.Core;

/// <summary>操作历史与播放历史，写入歌单级和全局日志。</summary>
public static class HistoryService
{
    private static string Timestamp() => DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");

    private static string Resolve(string playlistId)
        => string.IsNullOrEmpty(playlistId) ? ConfigService.GetCurrentPlaylistId() : playlistId;

    public static void RecordOperation(string action, string details = "", string result = "成功", string playlistId = null)
    {
        var pid = Resolve(playlistId);
        var line = $"[{Timestamp()}] {action} - {details} - 结果: {result}";
        if (!string.IsNullOrEmpty(pid))
        {
            YamlStore.AppendLine(AppPaths.OperateHistoryFile(pid), line);
        }
        YamlStore.AppendLine(AppPaths.GlobalOperateHistoryFile, $"[{pid ?? "-"}] {line}");
    }

    public static void RecordPlay(Song song, string playlistId = null)
    {
        var pid = Resolve(playlistId);
        var name = string.IsNullOrEmpty(song?.SongName) ? "未知" : song.SongName;
        var artist = string.IsNullOrEmpty(song?.Artist) ? "未知" : song.Artist;
        var requester = string.IsNullOrEmpty(song?.RequestedBy) ? "未知" : song.RequestedBy;
        var line = $"[{Timestamp()}] 播放 - 歌曲: {name} - 歌手: {artist} - 点歌人: {requester}";
        if (!string.IsNullOrEmpty(pid))
        {
            YamlStore.AppendLine(AppPaths.PlayHistoryFile(pid), line);
        }
        YamlStore.AppendLine(AppPaths.GlobalPlayHistoryFile, $"[{pid ?? "-"}] {line}");
        IncrementPlayCount();
    }

    private static void IncrementPlayCount()
    {
        var stats = YamlStore.Load<SystemStats>(AppPaths.SystemStatsFile) ?? new SystemStats();
        stats.TotalPlays++;
        stats.LastPlayTime = Timestamp();
        YamlStore.Save(AppPaths.SystemStatsFile, stats);
    }

    public static int GetPlayCount()
        => (YamlStore.Load<SystemStats>(AppPaths.SystemStatsFile) ?? new SystemStats()).TotalPlays;
}
