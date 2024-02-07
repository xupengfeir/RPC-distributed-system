# %%
import math
import os
import queue
import sys
import threading
import time

import matlab.engine
import rpyc
import rpyc.utils.server


class Computer:

    def __init__(self) -> None:
        self.IP = None
        self.Port = None
        self.Core = None
        self.Speed = None
        self.path = None
        self.model_name = None
        self.start_num = None
        self.end_num = None
        self.cal_num = None
        self.Remot = None

    # set
    def set_IP(self, IP):
        self.IP = IP

    def set_Port(self, Port):
        self.Port = Port

    def set_Core(self, Core):
        self.Core = Core

    def set_Speed(self, Speed):
        self.Speed = Speed

    def set_path(self, path):
        self.path = path

    def set_model_name(self, model_name):
        self.model_name = model_name

    def set_start_num(self, start_num):
        self.start_num = start_num

    def set_end_num(self, end_num):
        self.end_num = end_num

    def set_cal_num(self, cal_num):
        self.cal_num = cal_num

    # get
    def get_IP(self):
        return self.IP

    def get_Port(self):
        return self.Port

    def get_Core(self):
        return self.Core

    def get_Speed(self):
        return self.Speed

    def get_path(self):
        return self.path

    def get_model_name(self):
        return self.model_name

    def get_start_num(self):
        return self.start_num

    def get_end_num(self):
        return self.end_num

    def get_cal_num(self):
        return self.cal_num

    # 远程计算机
    def set_Remot(self, c):
        self.Remot = c

    def get_Remot(self):
        return self.Remot


class Model:
    # set
    def set_path(self, path):
        self.path = path

    def set_val_list(self, val_list):
        self.val_list = val_list

    def set_model_name(self, model_name):
        self.model_name = model_name

    def set_max_val(self, max_val):
        self.max_val = max_val

    def set_min_val(self, min_val):
        self.min_val = min_val

    def set_cal_time(self, cal_time):
        self.cal_time = cal_time

    def set_total_times(self, total_times):
        self.total_times = total_times

    def set_cut_times(self, cut_times):
        self.cut_times = cut_times

    # get
    def get_path(self):
        return self.path

    def get_model_name(self):
        return self.model_name

    def get_cal_time(self):
        return self.cal_time

    def get_total_times(self):
        return self.total_times

    def get_val_list(self):
        return self.val_list

    def get_max_val(self):
        return self.max_val

    def get_min_val(self):
        return self.min_val

    def get_cut_times(self):
        return self.cut_times


def allocate_times_by_speed(computer_list, model_config):
    total_times = model_config.get_total_times()
    computer_core = []
    computer_speed = []
    for i in range(len(computer_list)):
        computer_core.append(computer_list[i].get_Core())
        computer_speed.append(computer_list[i].get_Speed())
    # 第一部分，分配到每台计算机
    a_allocate = []
    for i in range(len(computer_core)):
        d_temple1 = computer_core
        d_temple2 = computer_speed
        e_temple = 0
        for j in range(i, len(d_temple1)):
            e_temple += d_temple1[j]*d_temple2[j]
        b = math.ceil(((total_times-sum(a_allocate)) *
                      computer_speed[i] * computer_core[i])/e_temple)
        a_allocate.append(b)
    if sum(a_allocate) != total_times:
        a_allocate[0] += (total_times-sum(a_allocate))
    # 第二部分 分配到每个核心
    b_allocate = []
    for i in range(len(a_allocate)):
        c_allocate_per_core = []
        for j in range(computer_core[i]):
            d = math.ceil(
                (a_allocate[i]-sum(c_allocate_per_core))/(computer_core[i]-j))
            c_allocate_per_core.append(d)
        b_allocate.append(c_allocate_per_core)
    # 计算开始和结束的计数
    b_allocate_start = []
    b_allocate_end = []
    for i in range(len(b_allocate)):
        b_allocate_start.append(list(b_allocate[i]))
        b_allocate_end.append(list(b_allocate[i]))
    b_allocate_start[0][0] = 1
    b_allocate_end[-1][-1] = total_times
    summed_number = 0
    for i in range(len(b_allocate)):
        for j in range(len(b_allocate[i])):
            try:
                b_allocate_end[i][j] = summed_number+b_allocate[i][j]
                try:
                    b_allocate_start[i][j+1] = summed_number+b_allocate[i][j]+1
                except:
                    b_allocate_start[i+1][0] = summed_number+b_allocate[i][j]+1
            except:
                pass
            summed_number += b_allocate[i][j]
    return (a_allocate, b_allocate_start, b_allocate_end)


def get_cal_speed(computer_list, model_config):

    md_path = []
    for i in computer_list:
        md_path.append(i.get_path())
    model_name = model_config.get_model_name()              # 模型文件名称
    val_list = model_config.get_val_list()   # 搜索参数名称
    max_val = model_config.get_max_val()           # 参数最大值
    min_val = model_config.get_min_val()    # 参数最小值
    # 链接远程计算机
    remote_computer_handel = []
    for i in range(len(computer_list)):
        remote_computer_handel.append(rpyc.connect(computer_list[i].get_IP(
        ), computer_list[i].get_Port(), config={'sync_request_timeout': None}))
        computer_list[i].set_Remot(remote_computer_handel[i])

    # 计算速度测试
    # 程序热身
    str_of_the_day = 'tsting0'
    times_val = 2
    star_time = []
    end_time = []
    for i in range(len(computer_list)):
        star_time_a = []
        end_time_a = []
        for j in range(computer_core[i]):
            star_time_a.append(1)
            end_time_a.append(pow(times_val, len(val_list)))
        star_time.append(star_time_a)
        end_time.append(end_time_a)

    cc = []
    for i in range(len(computer_list)):
        cc.append(computer_list[i].get_Remot().root.run_matlab(
            md_path[i], model_name, val_list, max_val, min_val, times_val, star_time[i], end_time[i], str_of_the_day))

    # 第一次计算
    str_of_the_day = 'tsting1'
    spend_times1 = []
    times_val1 = 2
    star_time = []
    end_time = []
    for i in range(len(computer_list)):
        star_time_a = []
        end_time_a = []
        for j in range(computer_core[i]):
            star_time_a.append(1)
            end_time_a.append(pow(times_val1, len(val_list)))
        star_time.append(star_time_a)
        end_time.append(end_time_a)
    cc = []
    for i in range(len(computer_list)):
        a = time.clock()
        cc1 = rpyc.async_(computer_list[i].get_Remot().root.run_matlab)
        cc.append(cc1(md_path[i], model_name, val_list, max_val, min_val,
                  times_val1, star_time[i], end_time[i], str_of_the_day))
        cc[i].wait()
        b = time.clock()
        spend_times1.append(b-a)

    # 第二次计算
    str_of_the_day = 'tsting2'
    spend_times2 = []
    times_val2 = 4
    star_time = []
    end_time = []
    for i in range(len(computer_list)):
        star_time_a = []
        end_time_a = []
        for j in range(computer_core[i]):
            star_time_a.append(1)
            end_time_a.append(pow(times_val2, len(val_list)))
        star_time.append(star_time_a)
        end_time.append(end_time_a)
    cc = []
    for i in range(len(computer_list)):
        a = time.clock()
        cc1 = rpyc.async_(computer_list[i].get_Remot().root.run_matlab)
        cc.append(cc1(md_path[i], model_name, val_list, max_val, min_val,
                  times_val2, star_time[i], end_time[i], str_of_the_day))
        cc[i].wait()
        b = time.clock()
        spend_times2.append(b-a)

    for i in remote_computer_handel:
        i.close()

    # 计算平均时间
    time_bar = []
    # time_X = [] 不计算
    for i in range(len(computer_list)):
        time_bar1 = (spend_times2[i] - spend_times1[i]) / (pow(times_val2, len(val_list)) - pow(times_val1, len(val_list)))
        time_bar.append(time_bar1)
        del time_bar1
        computer_list[i].set_Speed(1/time_bar[i])
    return time_bar


def conv_time_to_times_by_speed(computer_list, model_config):
    total_times_hat = 0
    for i in range(len(computer_list)):
        total_times_hat += computer_list[i].get_Speed() * \
            model_config.get_cal_time()*computer_list[i].get_Core()
    a = len(model_config.get_val_list())
    b = math.floor(pow(total_times_hat, 1/a))
    c = float(pow(b, a))
    return (c, b)


def calculate_values_by_allocated(computer_list, model_config, str_of_the_day):
    # 通用参数
    #md_path = model_config.get_path()
    md_path = []
    for i in computer_list:
        md_path.append(i.get_path())
    model_name = model_config.get_model_name()
    val_list = model_config.get_val_list()
    max_val = model_config.get_max_val()
    min_val = model_config.get_min_val()

    remote_computer_handel = []
    for i in range(len(computer_list)):
        remote_computer_handel.append(rpyc.connect(computer_list[i].get_IP(
        ), computer_list[i].get_Port(), config={'sync_request_timeout': None}))
        # computer_list[i].set_Remot(remote_computer_handel[i])

    cc = []
    for i in range(len(computer_list)):
        times_val1 = model_config.get_cut_times()
        star_time = computer_list[i].get_start_num()
        end_time = computer_list[i].get_end_num()
        cc1 = rpyc.async_(remote_computer_handel[i].root.run_matlab)
        cc.append(cc1(md_path[i], model_name, val_list, max_val,
                  min_val, times_val1, star_time, end_time, str_of_the_day))
        cc[i].ready
    for i in cc:
        i.wait()

    for i in remote_computer_handel:
        i.close()


def list_max(my_index, my_list):
    index = my_index[0]
    max_val = my_list[0]
    for i in range(len(my_index)):
        if max_val < my_list[i]:
            max_val = my_list[i]
            index = my_index[i]
    return (index, max_val)


def list_min(my_index, my_list):
    index = my_index[0]
    min_val = my_list[0]
    for i in range(len(my_index)):
        if min_val > my_list[i]:
            min_val = my_list[i]
            index = my_index[i]
    return (index, min_val)


def get_aim_values_by_function(computer_list, str_of_the_day):
    CC = []
    DD = []
    remote_computer_handel = []
    for i in range(len(computer_list)):
        remote_computer_handel.append(rpyc.connect(computer_list[i].get_IP(
        ), computer_list[i].get_Port(), config={'sync_request_timeout': None}))

    for i in remote_computer_handel:
        (C, D) = i.root.matlab_read(str_of_the_day)
        CC.append(C)
        DD.append(D)
    DDD = []
    CCC = []
    for i in CC:
        
        for j in i:
            CCC.append(j[0])
    for i in DD:
        for j in i:
            DDD.append(j[0])
    (CCCC, DDDD) = list_min(CCC, DDD)
    for i in remote_computer_handel:
        i.close()
    return (CCCC, DDDD)


def Multi_thread_calculate(computer_list, model_config, str_of_the_day):
    md_path = []
    for i in computer_list:
        md_path.append(i.get_path())
    model_name = model_config.get_model_name()
    val_list = model_config.get_val_list()
    max_val = model_config.get_max_val()
    min_val = model_config.get_min_val()

    remote_computer_handel = []
    for i in range(len(computer_list)):
        remote_computer_handel.append(rpyc.connect(computer_list[i].get_IP(
        ), computer_list[i].get_Port(), config={'sync_request_timeout': None}))

    th = []
    for i in range(len(remote_computer_handel)):
        star_time = computer_list[i].get_start_num()
        end_time = computer_list[i].get_end_num()
        times_val = model_config.get_cut_times()
        th.append(threading.Thread(target=remote_computer_handel[i].root.run_matlab, args=(
            md_path[i], model_name, val_list, max_val, min_val, times_val, star_time, end_time, str_of_the_day), daemon=False))
    for i in th:
        i.start()
    for i in th:
        i.join()
    for i in remote_computer_handel:
        i.close()


def get_aim_values_and_save_by_function(computer_list, str_of_the_day): 
    dir_path = 'C:\\grid_search_for_boost_parameters_lxr'
    os.chdir(dir_path)
    CC = []
    DD = []
    remote_computer_handel = []
    for i in range(len(computer_list)):
        remote_computer_handel.append(rpyc.connect(computer_list[i].get_IP(
        ), computer_list[i].get_Port(), config={'sync_request_timeout': None}))

    for i in remote_computer_handel:
        (C, D) = i.root.matlab_read(str_of_the_day)
        CC.append(C)
        DD.append(D)
    DDD = []
    CCC = []
    for i in CC:
        for j in i:
            CCC.append(j[0])
    for i in DD:
        for j in i:
            DDD.append(j[0])
    (CCCC, DDDD) = list_max(CCC, DDD)
    file_name = 'save'+str_of_the_day+'.csv'
    f = open(file_name, mode='w+', encoding='utf-8')
    f.write('index, value \n')
    for i in range(len(CCC)):
        save_str = str(CCC[i]) + ', ' + str(DDD[i])
        f.write(save_str + ' \n')
    f.close()
    for i in remote_computer_handel:
        i.close()
    return (CCCC, DDDD)


def Multi_thread_calculate_with_time(computer_list, model_config, str_of_the_day):
    md_path = []
    for i in computer_list:
        md_path.append(i.get_path())
    model_name = model_config.get_model_name()
    val_list = model_config.get_val_list()
    max_val = model_config.get_max_val()
    min_val = model_config.get_min_val()

    remote_computer_handel = []
    for i in range(len(computer_list)):
        remote_computer_handel.append(rpyc.connect(computer_list[i].get_IP(
        ), computer_list[i].get_Port(), config={'sync_request_timeout': None}))

    th = []
    for i in range(len(remote_computer_handel)):
        star_time = computer_list[i].get_start_num()
        end_time = computer_list[i].get_end_num()
        times_val = model_config.get_cut_times()
        th.append(threading.Thread(target=remote_computer_handel[i].root.run_matlab, args=(
            md_path[i], model_name, val_list, max_val, min_val, times_val, star_time, end_time, str_of_the_day), daemon=False))
    ticks = time.time()
    timessss = [ticks, ]
    for i in th:
        i.start()
        i.join()
        timessss.append(time.time())

    for i in remote_computer_handel:
        i.close()
    return timessss
# %%
if __name__ == "__main__":
    '''
    # 设定参数
    # str_of_the_day = '20210906'
    '''
# %%
    # str_of_the_day：是日期格式，用于设定保存文件名的类型
    str_of_the_day = time.strftime('%Y%m%d%H%M%S')
    # IP_list：IP地址列表
    IP_list = [ '192.168.1.6', ]
    # Port_list：IP地址对应端口列表 
    Port_list = ['12323', ]
    # Core_num：每台计算机的核心数 
    Core_num = [2, ]
    computer_core = Core_num
    md_path = ['C:\\grid_search_for_boost_parameters_lxr', ]  # 每台计算机中对应模型文件位置
    model_name = 'boot_model.slx' # 模型文件名称
    val_list = ['R', 'L', 'C',]   # 搜索参数名称
    min_val = [2, 200, 100, ]     # 参数最小值
    max_val = [4, 300, 300, ]     # 参数最大值
    cal_time_per_computer = 240  # 计算时间：(秒)

    # 初始化
    computer_list = []

    
    for i in range(len(IP_list)):
        temp_comp = Computer()
        computer_list.append(temp_comp)
        computer_list[i].set_IP(IP_list[i])
        computer_list[i].set_Port(Port_list[i])
        computer_list[i].set_Core(Core_num[i])
        computer_list[i].set_Speed(1)
        computer_list[i].set_path(md_path[i])

    model_config = Model()
    model_config.set_model_name(model_name)
    model_config.set_val_list(val_list)
    model_config.set_max_val(max_val)
    model_config.set_min_val(min_val)
    model_config.set_cal_time(cal_time_per_computer)
    # model_config.set_total_times(83521)
# %%
    # 以下开启并行计算，需要计时需要逐行执行
    (cal_speed) = get_cal_speed(computer_list, model_config)
    print(cal_speed)
# %%
    (total_times, cut_times) = conv_time_to_times_by_speed(
        computer_list, model_config)
    model_config.set_total_times(total_times)
    model_config.set_cut_times(cut_times)
    (a, start_num, end_num) = allocate_times_by_speed(computer_list, model_config)
    for i in range(len(computer_list)):
        computer_list[i].set_cal_num(a[i])
        computer_list[i].set_start_num(start_num[i])
        computer_list[i].set_end_num(end_num[i])
# %%
    Multi_thread_calculate(computer_list, model_config, str_of_the_day)
    # (match_index,best_match) = get_aim_values_by_function(computer_list, str_of_the_day) # 不保存取回结果
    (match_index, best_match) = get_aim_values_and_save_by_function(
        computer_list, str_of_the_day)
# %%
    import time
# localtime = time.localtime(time.time())



# %%
    timessssssss = Multi_thread_calculate_with_time(computer_list, model_config, str_of_the_day)
    print(timessssssss)

# %%

