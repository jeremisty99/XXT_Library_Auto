# XXT_Library_Auto 
**超星学习通图书馆系统自动化实现**
> 包括签到、预约、退座、暂离、查询空座位等功能 支持新旧两版系统

![svg](https://forthebadge.com/images/badges/made-with-python.svg)

![svg](https://forthebadge.com/images/badges/made-with-javascript.svg)

[![svg](https://shields.io/badge/BUILT%20BY-JERRY%20WANG-5da39d?logo=github&style=for-the-badge&logoWidth=20)](https://wangjiayi.cool)

主体部分基于**Doone-skser**的 <a href="https://github.com/Doone-skser/SSA">SSA项目</a>
在项目基础上进行了一些功能修改 (原项目现已关闭)

新增的滑动验证码部分 逻辑主要参考了**9cats**的 <a href="https://github.com/9cats/caviar">caviar项目</a> 具体识别部分采用了 <a href="https://github.com/sml2h3/ddddocr">ddddocr</a>完成

本项目仅供**学习参考**使用 项目代码质量较差且**不保证未来维护**

UPDATE: 2023-5-31 
1. 添加了对最新的enc加密字段的支持(check/enc()) 相关部分并未完善 有需要的同学可以自行修改
2. 测试发现旧版系统中取消了seatId字段 可能还有其他改动尚未发现 欢迎反馈

```diff
! 滥用本项目代码所导致的一切后果与作者本人无关 请勿用于非法用途
```
