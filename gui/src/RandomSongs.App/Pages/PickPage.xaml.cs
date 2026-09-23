using System.Collections.ObjectModel;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using RandomSongs.Core;

namespace RandomSongs.App.Pages;

public sealed partial class PickPage : Page
{
    private readonly ObservableCollection<Song> _songs = new();
    private List<KeyValuePair<string, PlaylistEntry>> _playlists = new();
    private string? _currentPlaylistId;
    private string? _resultUrl;
    private Song? _resultSong;
    private bool _suppressCombo;

    public PickPage()
    {
        InitializeComponent();
        SongList.ItemsSource = _songs;
        Loaded += (_, _) => RefreshAll();
    }

    private void RefreshAll()
    {
        _playlists = ConfigService.GetPlaylists();
        _currentPlaylistId = ConfigService.GetCurrentPlaylistId();
        PopulatePlaylistCombo();
        LoadSongs();
        UpdatePreventionText();
        ClearResult();
    }

    private void PopulatePlaylistCombo()
    {
        _suppressCombo = true;
        PlaylistCombo.Items.Clear();
        foreach (var entry in _playlists)
        {
            PlaylistCombo.Items.Add(entry.Value?.Name ?? entry.Key);
        }
        var index = _playlists.FindIndex(kv => kv.Key == _currentPlaylistId);
        PlaylistCombo.SelectedIndex = index >= 0 ? index : (_playlists.Count > 0 ? 0 : -1);
        _suppressCombo = false;
    }

    private void LoadSongs()
    {
        _songs.Clear();
        if (!string.IsNullOrEmpty(_currentPlaylistId))
        {
            foreach (var song in SongService.LoadSongs(_currentPlaylistId))
            {
                _songs.Add(song);
            }
        }
        SongCountText.Text = $"共 {_songs.Count} 首";
    }

    private void UpdatePreventionText()
    {
        if (string.IsNullOrEmpty(_currentPlaylistId))
        {
            PreventionText.Text = string.Empty;
            return;
        }
        var prevention = ConfigService.GetPrevention(_currentPlaylistId);
        if (!prevention.Enabled)
        {
            PreventionText.Text = "防重复：关闭";
            return;
        }
        var mode = prevention.Mode == "time_window" ? $"{prevention.TimeWindowMinutes} 分钟窗口" : "整轮不重复";
        PreventionText.Text = $"防重复：{mode}（已记录 {prevention.PlayedSongs.Count} 首）";
    }

    private void ClearResult()
    {
        _resultUrl = null;
        _resultSong = null;
        ResultSource.Text = string.Empty;
        PlayLocalButton.Visibility = Visibility.Collapsed;
        ResultPanel.Visibility = Visibility.Collapsed;
        EmptyHint.Visibility = Visibility.Visible;
    }

    private void PlaylistCombo_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_suppressCombo)
        {
            return;
        }
        var index = PlaylistCombo.SelectedIndex;
        if (index < 0 || index >= _playlists.Count)
        {
            return;
        }
        _currentPlaylistId = _playlists[index].Key;
        ConfigService.SetCurrentPlaylist(_currentPlaylistId);
        HistoryService.RecordOperation("切换歌单", $"切换到 '{_playlists[index].Value?.Name}'", playlistId: _currentPlaylistId);
        LoadSongs();
        UpdatePreventionText();
        ClearResult();
    }

    private void Reload_Click(object sender, RoutedEventArgs e)
    {
        LoadSongs();
        UpdatePreventionText();
    }

    private void PickButton_Click(object sender, RoutedEventArgs e)
    {
        if (string.IsNullOrEmpty(_currentPlaylistId))
        {
            return;
        }

        var song = PreventionService.Pick(_currentPlaylistId, _songs);
        if (song == null)
        {
            _resultUrl = null;
            _resultSong = null;
            ResultPanel.Visibility = Visibility.Visible;
            ResultName.Text = "没有可用的歌曲";
            ResultMeta.Text = "歌单为空，或都在防重复窗口内且未开启自动重置";
            ResultSource.Text = string.Empty;
            ResultUrl.Text = string.Empty;
            PlayLocalButton.Visibility = Visibility.Collapsed;
            OpenLinkButton.IsEnabled = false;
            EmptyHint.Visibility = Visibility.Collapsed;
            return;
        }

        HistoryService.RecordPlay(song, _currentPlaylistId);
        UpdatePreventionText();

        var config = ConfigService.Load();
        var localPlayback = config.LocalPlayback ?? new LocalPlaybackSettings();
        var playedLocal = localPlayback.Enabled && LocalPlaybackService.Play(song);
        ShowResult(song, playedLocal);

        if (!playedLocal)
        {
            var autoJump = config.AutoJump ?? new AutoJumpSettings();
            if (autoJump.Enabled)
            {
                var url = AutoJumpService.BuildUrl(song, autoJump);
                if (!string.IsNullOrEmpty(url))
                {
                    _ = OpenAfterDelayAsync(url, Math.Max(0, autoJump.Delay));
                }
            }
        }
    }

    private void ShowResult(Song song, bool playedLocal)
    {
        _resultSong = song;
        var autoJump = ConfigService.Load().AutoJump ?? new AutoJumpSettings();
        _resultUrl = AutoJumpService.BuildUrl(song, autoJump);

        ResultName.Text = song.SongName;
        ResultMeta.Text =
            $"歌手: {(string.IsNullOrEmpty(song.Artist) ? "未知" : song.Artist)}    " +
            $"点歌人: {(string.IsNullOrEmpty(song.RequestedBy) ? "未知" : song.RequestedBy)}";

        var hasLocal = LocalPlaybackService.HasLocalFile(song);
        PlayLocalButton.Visibility = hasLocal ? Visibility.Visible : Visibility.Collapsed;
        ResultSource.Text = hasLocal
            ? $"本地文件: {song.LocalPath}{(playedLocal ? "（已调用本地播放器）" : "")}"
            : string.Empty;

        ResultUrl.Text = string.IsNullOrEmpty(_resultUrl) ? string.Empty : _resultUrl;
        OpenLinkButton.IsEnabled = !string.IsNullOrEmpty(_resultUrl);
        ResultPanel.Visibility = Visibility.Visible;
        EmptyHint.Visibility = Visibility.Collapsed;
    }

    private void PlayLocalButton_Click(object sender, RoutedEventArgs e)
    {
        if (_resultSong is not null)
        {
            LocalPlaybackService.Play(_resultSong);
        }
    }

    private async Task OpenAfterDelayAsync(string url, int seconds)
    {
        if (seconds > 0)
        {
            await Task.Delay(TimeSpan.FromSeconds(seconds));
        }
        AutoJumpService.Open(url);
    }

    private void OpenLinkButton_Click(object sender, RoutedEventArgs e)
    {
        if (!string.IsNullOrEmpty(_resultUrl))
        {
            AutoJumpService.Open(_resultUrl);
        }
    }
}
