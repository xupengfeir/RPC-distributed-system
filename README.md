RPYC实现远程通信。利用RPYC实现远程多核心并行计算，对控制系统的控制器参数进行整定的方法。  

1. 服务器端配置.md介绍了开启RPyC通信所需要的服务端配置。
2. remote_grid_search_boost_p.py是服务器端运行脚本；  
3. local_grid_search_boost_p.py是本地客户端运行脚本；  
4. boost_model.slx是升压电路模型，grid_search_py.m设置仿真计算的内容。

整体实现的功能：  
求出boost模型最佳的电路参数R、L、C；由于参数的搜索空间较大，可以在本地将整个参数空间分配为几个子空间作为子计算任务，按照服务器端当前计算核心的计算负载给计算核心分配计算任务。
