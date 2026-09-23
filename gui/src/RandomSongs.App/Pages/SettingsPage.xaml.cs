using System.Linq;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using RandomSongs.Core;

namespace RandomSongs.App.Pages;

public sealed partial class SettingsPage : Page
{
    private string? _playlistId;
    private bool _loading;

    public SettingsPage()
    {
        InitializeComponent();
        Loaded += (_, _) => Populate();
    }

    private void Populate()
    {
        _loading = true;
        _playlistId = ConfigService.GetCurrentPlaylistId();

        var prevention = ConfigService.GetPrevention(_playlistId);
        PrevEnabled.IsOn = prevention.Enabled;
        SelectTag(PrevMode, prevention.Mode);
        PrevWindow.Value = prevention.TimeWindowMinutes;
        PrevReset.IsOn = prevention.ResetOnAllPlayed;
        PrevAvoid.IsOn = prevention.AvoidImmediateRepeat;
        PrevInfo.Text = $"已记录播放 {prevention.PlayedSongs.Count} 首";

        var config = ConfigService.Load();
        var jump = config.AutoJump ?? new AutoJumpSettings();
        JumpEnabled.IsOn = jump.Enabled;
        SelectTag(JumpMode, jump.Mode);
        JumpUrl.Text = jump.CustomUrl;
        JumpDelay.Value = jump.Delay;
        JumpPrefer.IsOn = jump.PreferSearch;

        var qq = config.QqSync ?? new QqSyncSettings();
        QqEnabled.IsOn = qq.Enabled;
        QqAuto.IsOn = qq.AutoOnStart;
        QqId.Text = qq.PlaylistId;

        LocalPlaybackToggle.IsOn = (config.LocalPlayback ?? new LocalPlaybackSettings()).Enabled;

        DataPathText.Text = AppPaths.DataRoot;
        _loading = false;
    }

    private static string? TagOf(ComboBox box) => (box.SelectedItem as ComboBoxItem)?.Tag as string;

    private static void SelectTag(ComboBox box, string tag)
    {
        foreach (var item in box.Items.OfType<ComboBoxItem>())
        {
            if ((item.Tag as string) == tag)
            {
                box.SelectedItem = item;
                return;
            }
        }
        if (box.Items.Count > 0)
        {
            box.SelectedItem = box.Items[0];
        }
    }

    // ---- 防重复 ----

    private void SavePrevention()
    {
        if (_loading || string.IsNullOrEmpty(_playlistId))
        {
            return;
        }
        var prevention = ConfigService.GetPrevention(_playlistId);
        prevention.Enabled = PrevEnabled.IsOn;
        prevention.Mode = TagOf(PrevMode) ?? "time_window";
        prevention.TimeWindowMinutes = double.IsNaN(PrevWindow.Value) ? 60 : (int)PrevWindow.Value;
        prevention.ResetOnAllPlayed = PrevReset.IsOn;
        prevention.AvoidImmediateRepeat = PrevAvoid.IsOn;
        ConfigService.SavePrevention(_playlistId, prevention);
        PrevInfo.Text = $"已记录播放 {prevention.PlayedSongs.Count} 首";
    }

    private void Prev_Changed(object sender, RoutedEventArgs e) => SavePrevention();

    private void PrevNumber_Changed(NumberBox sender, NumberBoxValueChangedEventArgs args) => SavePrevention();

    private async void PrevReset_Click(object sender, RoutedEventArgs e)
    {
        if (string.IsNullOrEmpty(_playlistId))
        {
            return;
        }
        var prevention = ConfigService.GetPrevention(_playlistId);
        if (prevention.PlayedSongs.Count == 0)
        {
            PrevInfo.Text = "当前没有播放记录";
            return;
        }

        var confirm = new ContentDialog
        {
            Title = "重置播放记录",
            Content = $"将清除 {prevention.PlayedSongs.Count} 条记录，确定吗？",
            PrimaryButtonText = "重置",
            CloseButtonText = "取消",
            DefaultButton = ContentDialogButton.Close,
            XamlRoot = XamlRoot,
        };
        if (await confirm.ShowAsync() != ContentDialogResult.Primary)
        {
            return;
        }

        prevention.PlayedSongs = new List<PlayedRecord>();
        prevention.LastResetTime = PreventionService.Format(DateTime.Now);
        ConfigService.SavePrevention(_playlistId, prevention);
        HistoryService.RecordOperation("重置播放记录", $"清除记录: {prevention.PlayedSongs.Count}条", playlistId: _playlistId);
        Populate();
    }

    // ---- 自动跳转 ----

    private void SaveJump()
    {
        if (_loading)
        {
            return;
        }
        var jump = ConfigService.Load().AutoJump ?? new AutoJumpSettings();
        jump.Enabled = JumpEnabled.IsOn;
        jump.Mode = TagOf(JumpMode) ?? "search";
        jump.CustomUrl = JumpUrl.Text.Trim();
        jump.Delay = double.IsNaN(JumpDelay.Value) ? 3 : (int)JumpDelay.Value;
        jump.PreferSearch = JumpPrefer.IsOn;
        ConfigService.SaveAutoJump(jump);
    }

    private void Jump_Changed(object sender, RoutedEventArgs e) => SaveJump();

    private void JumpNumber_Changed(NumberBox sender, NumberBoxValueChangedEventArgs args) => SaveJump();

    private void JumpUrl_LostFocus(object sender, RoutedEventArgs e) => SaveJump();

    // ---- QQ 同步 ----

    private void SaveQq()
    {
        if (_loading)
        {
            return;
        }
        var config = ConfigService.Load();
        var qq = config.QqSync ?? new QqSyncSettings();
        qq.Enabled = QqEnabled.IsOn;
        qq.AutoOnStart = QqAuto.IsOn;
        qq.PlaylistId = QqId.Text.Trim();
        config.QqSync = qq;
        ConfigService.Save(config);
    }

    private void Qq_Changed(object sender, RoutedEventArgs e) => SaveQq();

    // ---- 本地播放 ----

    private void LocalPlayback_Changed(object sender, RoutedEventArgs e)
    {
        if (_loading)
        {
            return;
        }
        var localPlayback = ConfigService.GetLocalPlayback();
        localPlayback.Enabled = LocalPlaybackToggle.IsOn;
        ConfigService.SaveLocalPlayback(localPlayback);
    }

    private void QqId_LostFocus(object sender, RoutedEventArgs e) => SaveQq();

    private async void QqSync_Click(object sender, RoutedEventArgs e)
    {
        SaveQq();
        QqInfo.Text = "正在同步...";
        try
        {
            var (added, total) = await QqPlaylistService.SyncAsync();
            QqInfo.Text = $"同步完成：新增 {added} 首，当前歌单共 {total} 首";
        }
        catch (Exception ex)
        {
            QqInfo.Text = $"同步失败：{ex.Message}";
        }
    }

    private async void QqImport_Click(object sender, RoutedEventArgs e)
    {
        SaveQq();
        if (string.IsNullOrWhiteSpace(QqId.Text))
        {
            QqInfo.Text = "请先填写 QQ 歌单 ID 或分享链接";
            return;
        }

        var nameBox = new TextBox { Header = "新歌单名称", Text = "QQ歌单", Width = 320 };
        var dialog = new ContentDialog
        {
            Title = "拉取为新歌单",
            Content = nameBox,
            PrimaryButtonText = "导入",
            CloseButtonText = "取消",
            DefaultButton = ContentDialogButton.Primary,
            XamlRoot = XamlRoot,
        };
        if (await dialog.ShowAsync() != ContentDialogResult.Primary)
        {
            return;
        }

        QqInfo.Text = "正在拉取...";
        try
        {
            var (playlistId, added) = await QqPlaylistService.ImportAsync(
                QqId.Text.Trim(),
                newPlaylistName: nameBox.Text.Trim());
            var name = ConfigService.GetPlaylist(playlistId)?.Name ?? playlistId;
            QqInfo.Text = $"已导入为新歌单「{name}」：{added} 首";
        }
        catch (Exception ex)
        {
            QqInfo.Text = $"导入失败：{ex.Message}";
        }
    }
}
