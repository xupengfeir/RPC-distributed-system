import os
import queue
import threading

import matlab.engine
import rpyc
import rpyc.utils.server


def compute(md_path, model_name, val_list, max_val, min_val, times_val, star_time, end_time, 
            thread_name, str_of_the_day, q):
    os.chdir(md_path)
    eng = matlab.engine.start_matlab()
    eng.cd(md_path, nargout=0)
    C = eng.grid_search_py(md_path, model_name, val_list, max_val, min_val,
                           times_val, star_time, end_time, 8001, thread_name, str_of_the_day)
    eng.quit()
    q.put(C)


def per_compute(md_path, model_name, val_list, max_val, min_val, times_val, star_time, end_time, 
                thread_name, str_of_the_day):
    os.chdir(md_path)
    eng = matlab.engine.start_matlab()
    eng.cd(md_path, nargout=0)
    C = eng.grid_search_py(md_path, model_name, val_list, max_val, min_val,
                           times_val, star_time, end_time, 8001, thread_name, str_of_the_day)
    eng.quit()


class newRpycRemote(rpyc.Service):
    def on_connect(self, conn):
        return super().on_connect(conn)

    def on_disconnect(self, conn):
        return super().on_disconnect(conn)

    def exposed_run_matlab(self, md_path, model_name, val_list,
                            max_val, min_val, times_val, 
                            star_time, end_time, str_of_the_day):
        # 类型转换
        if type(val_list) is not list:
            cov_val_list = []
            cov_max_val = []
            cov_min_val = []
            for i in range(len(val_list)):
                cov_val_list.append(val_list[i])
                cov_max_val.append(max_val[i])
                cov_min_val.append(min_val[i])
            val_list = cov_val_list
            max_val = cov_max_val
            min_val = cov_min_val
        th = []
        th_result = []
        q = queue.Queue()
        for i in range(len(star_time)):
            thread_name = 'a' + str(i)
            th.append(threading.Thread(target=compute, args=(md_path, model_name, val_list, 
                    max_val, min_val, times_val, star_time[i], end_time[i], thread_name, 
                    str_of_the_day, q), name='a'+str(i), daemon=False))
            th[i].start()
        for i in range(len(star_time)):
            th[i].join()
        for _ in range(len(star_time)):
            th_result.append(q.get())
        return th_result

    def exposed_matlab_read(self, filename_char):
        eng = matlab.engine.start_matlab()
        (C, D) = eng.read_files(filename_char, nargout=2)
        eng.quit()
        return (C, D)


if __name__ == '__main__':
    s = rpyc.utils.server.ThreadedServer(
        newRpycRemote, port=12323, auto_register=False)
    s.start()
# %%



