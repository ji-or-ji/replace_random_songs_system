using RandomSongs.Core;
using Xunit;

namespace RandomSongs.Core.Tests;

public class PreventionTests : TempDataTest
{
    private void Set(Action<DuplicatePrevention> mutate)
    {
        var prevention = ConfigService.GetPrevention("default");
        mutate(prevention);
        ConfigService.SavePrevention("default", prevention);
    }

    [Fact]
    public void CycleHasNoRepeatUntilAllPlayed()
    {
        Set(p =>
        {
            p.Enabled = true;
            p.Mode = "cycle";
            p.AvoidImmediateRepeat = false;
            p.ResetOnAllPlayed = true;
        });

        var songs = SongService.LoadSongs("default");
        var seen = new HashSet<string>();
        for (var i = 0; i < songs.Count; i++)
        {
            var picked = PreventionService.Pick("default", songs);
            Assert.NotNull(picked);
            seen.Add(picked!.Id);
        }
        Assert.Equal(songs.Count, seen.Count);
        Assert.NotNull(PreventionService.Pick("default", songs)); // 全部播完后应重置再选
    }

    [Fact]
    public void TimeWindowWithoutResetReturnsNull()
    {
        Set(p =>
        {
            p.Enabled = true;
            p.Mode = "time_window";
            p.TimeWindowMinutes = 60;
            p.AvoidImmediateRepeat = false;
            p.ResetOnAllPlayed = false;
        });

        var songs = SongService.LoadSongs("default");
        for (var i = 0; i < songs.Count; i++)
        {
            Assert.NotNull(PreventionService.Pick("default", songs));
        }
        Assert.Null(PreventionService.Pick("default", songs));
    }

    [Fact]
    public void CorruptRecordsAreSkipped()
    {
        Set(p => { p.Enabled = true; p.Mode = "time_window"; });

        var prevention = ConfigService.GetPrevention("default");
        prevention.PlayedSongs = new List<PlayedRecord>
        {
            new() { SongId = "no-such-id", SongName = "幽灵", PlayTime = "坏时间戳" },
            new() { SongId = null, SongName = "空id", PlayTime = "2020-01-01 00:00:00" },
        };
        ConfigService.SavePrevention("default", prevention);

        Assert.NotNull(PreventionService.Pick("default", SongService.LoadSongs("default")));
    }

    [Fact]
    public void RecordsStayBounded()
    {
        Set(p =>
        {
            p.Enabled = true;
            p.Mode = "time_window";
            p.TimeWindowMinutes = 60;
            p.AvoidImmediateRepeat = false;
        });

        var prevention = ConfigService.GetPrevention("default");
        prevention.PlayedSongs = new List<PlayedRecord>
        {
            new() { SongId = "x", SongName = "旧", PlayTime = "2000-01-01 00:00:00" },
        };
        ConfigService.SavePrevention("default", prevention);

        PreventionService.Pick("default", SongService.LoadSongs("default"));
        Assert.True(ConfigService.GetPrevention("default").PlayedSongs.Count <= 5);
    }

    [Fact]
    public void DisabledPreventionStillPicks()
    {
        Set(p => { p.Enabled = false; });
        Assert.NotNull(PreventionService.Pick("default", SongService.LoadSongs("default")));
    }
}
