# Gate9 分域最小增量实现

按已批准 `G9-DOMAIN-QUALIFICATION/0.1.0` 在main内联执行，不另建worktree，不委派。
使用研究协议、TDD与实现计划流程；设计已批准，不重新请求普通工程授权。

- [x] G1：真实文件fixture验证预声明profile、必要成员/依赖边双模式一致、三窗独立手算及缺证据拒绝；新增版本封套复用现有Engineering S/A入口，不升级历史资格。
- [x] N1：producer记录持有的显式流生命周期及current-stream调用；Canonical将marker内API/correlation与实际activity/sync绑定，核对context/线程/ownership；复用物理S/B。缺marker、错流/身份、缺correlation反例。
- [x] 最小受控目标桥接准备：两个request各两token、kernel→D2H→PyTorch current-stream synchronize；初始化/drain窗外，微程序warmup_count=0；保留上一measured request物理前缀，独立必要集合及token预期。CPU只测编排与失败，不运行CUDA。合同首选新建专用流，未扩展旧schema到warmup来源。
- [x] 相关回归、静态/差异检查；更新进度与交接，同次提交。固定提交后生成单一增量交付包及一次执行/单ZIP回传脚本，目标审查前不执行。旧资格回归一项基线失败已独立复现并记录，不改旧oracle追绿。

不改变S/A/B公式、旧读取路径或warning门；Gate8 PASS，Gate9待实物审查。长度仅逐request检查，不自动全Q0。
