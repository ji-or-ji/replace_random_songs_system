using Xunit;

// Core 的路径/数据根是进程级静态状态，禁用并行以免相互干扰
[assembly: CollectionBehavior(DisableTestParallelization = true)]
