using System.Collections.ObjectModel;
using System.Linq;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using RandomSongs.Core;

namespace RandomSongs.App.Pages;

public sealed partial class SongsPage : Page
{
    private readonly ObservableCollection<Song> _songs = new();
    private string? _playlistId;

    public SongsPage()
    {
        InitializeComponent();
        SongList.ItemsSource = _songs;
        Loaded += (_, _) => Load();
    }

    private void Load()
    {
        _playlistId = ConfigService.GetCurrentPlaylistId();
        _songs.Clear();
        if (!string.IsNullOrEmpty(_playlistId))
        {
            foreach (var song in SongService.LoadSongs(_playlistId))
            {
                _songs.Add(song);
            }
        }
        var name = string.IsNullOrEmpty(_playlistId) ? "-" : ConfigService.GetPlaylist(_playlistId)?.Name ?? _playlistId;
        HeaderText.Text = $"歌曲管理 · {name}（{_songs.Count} 首）";
    }

    private void Refresh_Click(object sender, RoutedEventArgs e) => Load();

    private async void Add_Click(object sender, RoutedEventArgs e)
    {
        if (string.IsNullOrEmpty(_playlistId))
        {
            return;
        }
        var editor = BuildEditor(null);
        if (await editor.Dialog.ShowAsync() != ContentDialogResult.Primary)
        {
            return;
        }
        var songs = SongService.LoadSongs(_playlistId);
        var now = SongService.Now();
        var song = SongService.Normalize(new Song
        {
            SongName = editor.NameBox.Text.Trim(),
            Artist = editor.ArtistBox.Text.Trim(),
            Url = editor.UrlBox.Text.Trim(),
            LocalPath = editor.LocalPathBox.Text.Trim(),
            RequestedBy = editor.SelectedRequester,
            CreatedAt = now,
            LastModified = now,
        });
        songs.Add(song);
        SongService.SaveSongs(_playlistId, songs);
        HistoryService.RecordOperation(
            "添加歌曲",
            $"歌曲: {song.SongName} - 歌手: {song.Artist} - 点歌人: {song.RequestedBy}",
            playlistId: _playlistId);
        Load();
    }

    private async void Edit_Click(object sender, RoutedEventArgs e)
    {
        if (SongList.SelectedItem is not Song selected)
        {
            await ShowMessage("请先选择一首歌曲");
            return;
        }

        var editor = BuildEditor(selected);
        if (await editor.Dialog.ShowAsync() != ContentDialogResult.Primary)
        {
            return;
        }

        var original = selected.SongName;
        selected.SongName = editor.NameBox.Text.Trim();
        selected.Artist = editor.ArtistBox.Text.Trim();
        selected.Url = editor.UrlBox.Text.Trim();
        selected.LocalPath = editor.LocalPathBox.Text.Trim();
        selected.RequestedBy = editor.SelectedRequester;
        selected.LastModified = SongService.Now();

        SongService.SaveSongs(_playlistId!, _songs.ToList());
        HistoryService.RecordOperation("修改歌曲", $"歌曲: {original} -> {selected.SongName}", playlistId: _playlistId);
        Load();
    }

    private async void Delete_Click(object sender, RoutedEventArgs e)
    {
        if (SongList.SelectedItem is not Song selected)
        {
            await ShowMessage("请先选择一首歌曲");
            return;
        }

        var confirm = new ContentDialog
        {
            Title = "删除歌曲",
            Content = $"确定删除「{selected.SongName}」吗？此操作不可恢复。",
            PrimaryButtonText = "删除",
            CloseButtonText = "取消",
            DefaultButton = ContentDialogButton.Close,
            XamlRoot = XamlRoot,
        };
        if (await confirm.ShowAsync() != ContentDialogResult.Primary)
        {
            return;
        }

        _songs.Remove(selected);
        SongService.SaveSongs(_playlistId!, _songs.ToList());
        HistoryService.RecordOperation("删除歌曲", $"歌曲: {selected.SongName}", playlistId: _playlistId);
        Load();
    }

    private SongEditor BuildEditor(Song? existing)
    {
        var editor = new SongEditor
        {
            NameBox = { Header = "歌曲名称", Text = existing?.SongName ?? "" },
            ArtistBox = { Header = "歌手（可空）", Text = existing?.Artist ?? "" },
            UrlBox = { Header = "链接（可空）", Text = existing?.Url ?? "" },
            LocalPathBox = { Header = "本地文件路径（可空）", Text = existing?.LocalPath ?? "" },
        };
        editor.RequesterBox.Header = "点歌人";
        editor.RequesterBox.HorizontalAlignment = HorizontalAlignment.Stretch;
        editor.RequesterBox.Items.Add("未知");
        if (!string.IsNullOrEmpty(_playlistId))
        {
            foreach (var requester in PlaylistService.LoadRequesters(_playlistId))
            {
                if (!string.IsNullOrWhiteSpace(requester.Name))
                {
                    editor.RequesterBox.Items.Add(requester.Name);
                }
            }
        }
        var current = existing?.RequestedBy;
        if (!string.IsNullOrWhiteSpace(current) && !editor.RequesterBox.Items.Contains(current))
        {
            editor.RequesterBox.Items.Add(current);
        }
        editor.RequesterBox.SelectedItem = string.IsNullOrWhiteSpace(current) ? "未知" : current;

        var panel = new StackPanel { Spacing = 10, Width = 380 };
        panel.Children.Add(editor.NameBox);
        panel.Children.Add(editor.ArtistBox);
        panel.Children.Add(editor.UrlBox);
        panel.Children.Add(editor.LocalPathBox);
        panel.Children.Add(editor.RequesterBox);

        editor.Dialog.Title = existing == null ? "添加歌曲" : "编辑歌曲";
        editor.Dialog.Content = panel;
        editor.Dialog.PrimaryButtonText = "保存";
        editor.Dialog.CloseButtonText = "取消";
        editor.Dialog.DefaultButton = ContentDialogButton.Primary;
        editor.Dialog.XamlRoot = XamlRoot;
        editor.Dialog.IsPrimaryButtonEnabled = !string.IsNullOrWhiteSpace(editor.NameBox.Text);
        editor.NameBox.TextChanged += (_, _) =>
            editor.Dialog.IsPrimaryButtonEnabled = !string.IsNullOrWhiteSpace(editor.NameBox.Text);
        return editor;
    }

    private async Task ShowMessage(string message)
    {
        var dialog = new ContentDialog
        {
            Title = "提示",
            Content = message,
            CloseButtonText = "好",
            XamlRoot = XamlRoot,
        };
        await dialog.ShowAsync();
    }

    private sealed class SongEditor
    {
        public TextBox NameBox { get; } = new();
        public TextBox ArtistBox { get; } = new();
        public TextBox UrlBox { get; } = new();
        public TextBox LocalPathBox { get; } = new();
        public ComboBox RequesterBox { get; } = new();
        public ContentDialog Dialog { get; } = new();

        public string SelectedRequester => RequesterBox.SelectedItem as string ?? "未知";
    }
}
