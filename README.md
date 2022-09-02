# blusterSpeed：开源的订阅测试工具

## 兼容性

- [x] sspanel后端
- [x] v2board后端

## 进度

- [x] 可视化
- [ ] 流媒体解锁检测
- [ ] 更多评估指标
- [ ] 对接Telegram Bot

## 部署

请安装speedtest-cli(Ookla)和matplotlib，并将Clash放置在`src`目录下（文件名`clash`）。  
自动下载地区信息：

```
python3 main.py <测试订阅链接>
```
手动指定地区信息：

```
python3 main.py -c <Country.mmdb文件位置> <测试订阅链接>
```

测试结果位于`result.png`。

## 注意事项

- 只支持GNU Linux与WSL 2
- matplotlib可能不能正确显示中文，需要手动配置字体文件

