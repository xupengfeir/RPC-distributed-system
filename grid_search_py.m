function total_save_name = grid_search_py(md_path, model_name, var_list, max_val, min_val, times_val, start_time, end_time, sim_len,thread_name, str_of_the_day)
%����matlab��������������
%   ͨ��matlabʵ�ֲ��м���
start_sim = 1501
bdclose;
%% Ĭ�ϲ���
if(~exist('sim_len','var'))
    simlenght = 8001;
else
    sim_len = double(sim_len);
    simlenght = sim_len;
end

if(~exist('thread_name','var'))
    thread_name = 'a1';
end

if(~exist('str_of_the_day','var'))
    str_of_the_day = 'nan_testing';
end

%% �жϸ�ʽ

if(isa(max_val,'cell')  )
    t_max_val = zeros(1,length(max_val));
    t_min_val = zeros(1,length(min_val));
    for i = 1 : length(max_val)
        t_max_val(i) = double(max_val{i});
        t_min_val(i) = double(min_val{i});
    end
    max_val = t_max_val;
    min_val = t_min_val;
    clear t_max_val t_min_val
    times_val = double(times_val);
    start_time = double(start_time);
    end_time = double(end_time);
    
end

%% ��ʼ������
parameter_array = zeros(length(max_val), times_val);
caltimes = end_time - start_time + 1;
for i = 1:length(max_val)
    parameter_array(i,:) = linspace(min_val(i), max_val(i), times_val);
end

%% �ļ��ָ�
cut_times = ceil(double(caltimes)/1024); % ȷ�����зָ����-1�Ĵ���
weishu = floor(log10(cut_times))+1; % ����Ҫ�����ļ���λ��
weishu_str = ['%0',num2str(weishu),'d'];
cut_times_times = 1024 * ones(1,cut_times-1);
cut_times_times(length(cut_times_times)+1) = mod(caltimes,1024);

%% ����ģ��
% old_path = cd;
cd(md_path);
try
    rmdir("savepath")
    mkdir savepath
catch
    mkdir savepath
end
load_system(model_name);

%% ����������

for idx = 1:cut_times
    idxx  = zeros(1, cut_times_times(idx));
    out_IAE= zeros(1, cut_times_times(idx));
    aaa = zeros(1, cut_times_times(idx));
    bbb =zeros(1, cut_times_times(idx));
    ccc =zeros(1, cut_times_times(idx));
    
    y_hat_save = zeros(simlenght-start_sim, cut_times_times(idx));
    y_real_save =zeros(simlenght-start_sim, cut_times_times(idx));
    
    
    for idx2 = 1:cut_times_times(idx)
        try
            idx3 = start_time + idx2 + sum(cut_times_times(1:idx-1)) - 1;
            so1 = zeros(1,length(var_list));
            so2 = transform2(idx3 - 1, times_val);
            
            for i = 1:length(so2)
                so1(end - i + 1) = so2(end - i + 1);
            end
            so1 = so1 + 1;
        catch
            save error_message.mat
            error('something wrong');
        end
        try
            for i = 1:length(var_list)
                assignin('caller',var_list{i},parameter_array(i,so1(i)));
            end
        catch
            % disp('error');
            so1 = so1 - 1;
            for dslkafja = 1:length(so1)
                if so1(dslkafja) == times_val
                    so1(dslkafja) = 0;
                    so1(dslkafja-1) = so1(dslkafja-1) + 1;
                end
            end
            so1 = so1 + 1;
            for i = 1:length(var_list)
                assignin('caller',var_list{i},parameter_array(i,so1(i)));
            end
        end
        
        outTemp = sim(model_name, 'SimulationMode', 'normal');
        
        %         y1 = outTemp.get('yout').get(1).Values.Data;
        %         y2 = outTemp.get('yout').get(4).Values.Data;
        %         u1 = outTemp.get('yout').get(2).Values.Data;
        %         u2 = outTemp.get('yout').get(5).Values.Data;
        y_hat = outTemp.get('yout').get(1).Values.Data(start_sim+1:end);
        y_real = outTemp.get('yout').get(3).Values.Data(start_sim+1:end);
        y_bar = mean(y_real);
        RR =max(0,1-sum( (y_real - y_hat).^2)/(sum( (y_real - y_bar).^2 )) ) ;
        
        %         iae01 = abs(y1 - u1);
        %         iae02 = abs(y2 - u2);
        %
        %         IAE1 = sum(iae01(1:end));
        %         IAE2 = sum(iae02(1:end));
        
        idxx(idx2) = idx3;
        out_IAE(idx2) = RR;
        i = 1;
        aaa(idx2) = parameter_array(i,so1(i));
        i = 2;
        bbb(idx2) =parameter_array(i,so1(i));
        i = 3;
        ccc(idx2) = parameter_array(i,so1(i));
        %         i = 4;
        %         ddd(idx2) = parameter_array(i,so1(i));
        y_hat_save(:,idx2) = y_hat(1:end);
        y_real_save(:,idx2) = y_real(1:end);
        %         y1save(:,idx2) = y1(1:end);
        %         y2save(:,idx2) = y2(1:end);
        %         u1save(:,idx2) = u1(1:end);
        %         u2save(:,idx2) = u2(1:end);
        
    end
    IAE = [idxx', aaa', bbb', ccc', out_IAE'];
    save_name = ['.\savepath\',thread_name,'-',str_of_the_day,num2str(idx,weishu_str),'-',num2str(cut_times,weishu_str),'.mat'];
    save(save_name,'y_hat_save','y_real_save','IAE');
    clear IAE y_hat_save y_real_save idx aaa ccc bbb out_IAE

end
total_save_name = {char([thread_name,'-',str_of_the_day])};
bdclose;
% cd(old_path);
end