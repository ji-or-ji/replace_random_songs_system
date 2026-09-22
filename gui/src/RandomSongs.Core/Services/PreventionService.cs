using System.Linq;

namespace RandomSongs.Core;

/// <summary>防重复选歌，行为对齐 Python 版的 pick_song。</summary>
public static class PreventionService
{
    private static readonly Random Rng = new();
    private static readonly string[] TimeFormats = { "yyyy-MM-dd HH:mm:ss", "yyyy/MM/dd HH:mm:ss" };

    // 同上：输出用斜杠格式，避免被当成 YAML 时间戳而让 PyYAML 读成 datetime
    public static string Format(DateTime moment) => moment.ToString("yyyy/MM/dd HH:mm:ss");

    public static DateTime? ParseTime(string value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return null;
        }
        return DateTime.TryParseExact(
            value.Trim(),
            TimeFormats,
            System.Globalization.CultureInfo.InvariantCulture,
            System.Globalization.DateTimeStyles.None,
            out var parsed)
            ? parsed
            : null;
    }

    private static List<PlayedRecord> CleanRecords(
        IEnumerable<PlayedRecord> records,
        HashSet<string> validIds,
        string mode,
        int windowSeconds,
        DateTime now)
    {
        var cleaned = new List<PlayedRecord>();
        foreach (var record in records ?? Enumerable.Empty<PlayedRecord>())
        {
            if (record == null || string.IsNullOrEmpty(record.SongId) || !validIds.Contains(record.SongId))
            {
                continue;
            }
            var playTime = ParseTime(record.PlayTime);
            if (playTime == null)
            {
                continue;
            }
            if (mode == "time_window" && (now - playTime.Value).TotalSeconds > windowSeconds)
            {
                continue;
            }
            cleaned.Add(new PlayedRecord
            {
                SongId = record.SongId,
                SongName = record.SongName ?? "",
                PlayTime = record.PlayTime,
            });
        }
        return cleaned;
    }

    /// <summary>按防重复策略选一首；无可选且不允许重置时返回 null。</summary>
    public static Song Pick(string playlistId, IEnumerable<Song> songs, bool persist = true)
    {
        var valid = SongService.FilterValid(songs);
        if (valid.Count == 0)
        {
            return null;
        }

        var prevention = ConfigService.GetPrevention(playlistId);
        if (!prevention.Enabled)
        {
            return valid[Rng.Next(valid.Count)];
        }

        var now = DateTime.Now;
        var windowSeconds = Math.Max(0, prevention.TimeWindowMinutes) * 60;
        var validIds = valid.Where(s => !string.IsNullOrEmpty(s.Id)).Select(s => s.Id).ToHashSet();

        var records = CleanRecords(prevention.PlayedSongs, validIds, prevention.Mode, windowSeconds, now);
        var blocked = records.Select(r => r.SongId).ToHashSet();
        if (prevention.AvoidImmediateRepeat && records.Count > 0)
        {
            blocked.Add(records[^1].SongId);
        }

        var available = valid.Where(s => !blocked.Contains(s.Id)).ToList();
        if (available.Count == 0)
        {
            if (prevention.ResetOnAllPlayed)
            {
                records = new List<PlayedRecord>();
                prevention.LastResetTime = Format(now);
                available = valid;
            }
            else
            {
                prevention.PlayedSongs = records;
                ConfigService.SavePrevention(playlistId, prevention);
                return null;
            }
        }

        var chosen = available[Rng.Next(available.Count)];
        if (!persist)
        {
            return chosen;
        }

        records.Add(new PlayedRecord
        {
            SongId = chosen.Id,
            SongName = chosen.SongName ?? "",
            PlayTime = Format(now),
        });
        prevention.PlayedSongs = records;
        ConfigService.SavePrevention(playlistId, prevention);
        return chosen;
    }
}
