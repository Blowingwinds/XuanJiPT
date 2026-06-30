# One-Command GitHub Push

在项目根目录 `C:\ptprojects` 的 PowerShell 中执行：

```powershell
git add -A; git commit -m "Update XuanJiPT"; git branch -M main; if (-not (git remote get-url origin 2>$null)) { git remote add origin https://github.com/Blowingwinds/XuanJiPT.git } else { git remote set-url origin https://github.com/Blowingwinds/XuanJiPT.git }; git push -u origin main
```

说明：

- 如果没有文件变化，`git commit` 会提示 nothing to commit，随后可单独执行 `git push -u origin main`。
- 推送 GitHub 需要本机已经配置可用的 GitHub 登录凭据或 token。
