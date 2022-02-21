import pandas as pd
import numpy as np
import os
import argparse


def parse_sram_read_data(elems):
    data = 0
    for i in range(len(elems)):
        e = elems[i]
        if e != ' ':
            data += 1

    return data


# These two sram trace files are read in for calculation, to dump the detail log
def gen_bw_numbers(sram_write_trace_file,
                   sram_read_trace_file
                   # sram_read_trace_file,
                   # array_h, array_w        # These are needed for utilization calculation
                   ):
    min_clk = 100000
    max_clk = -1
    detailed_log = ""

    '''
    sram ofmap (write)
    '''
    num_sram_ofmap_bytes = 0
    f = open(sram_write_trace_file, 'r')
    first = True

    for row in f:
        num_sram_ofmap_bytes += len(row.split(',')) - 2
        elems = row.strip().split(',')
        clk = float(elems[0])

        if first:
            first = False
            start_clk = clk

    stop_clk = clk

    # f: where sram ofmap write bytes are
    # fixme: son of a bitch, these gatech guys are really sloppy here, sram write bytes here push in
    #   and make into sram read bytes in the detail log...
    detailed_log += str(start_clk) + ",\t" + str(stop_clk) + ",\t" + str(num_sram_ofmap_bytes) + ",\t"
    f.close()
    print('as this layer, the num sram of write bytes is {}'.format(num_sram_ofmap_bytes))

    if clk > max_clk:
        max_clk = clk

    '''
    sram read
    '''
    num_sram_read_bytes = 0
    total_util = 0
    # print("Opening " + sram_trace_file)
    f = open(sram_read_trace_file, 'r')
    first = True

    for row in f:
        # num_sram_read_bytes += len(row.split(',')) - 2
        elems = row.strip().split(',')
        clk = float(elems[0])

        if first:
            first = False
            start_clk = clk

        # util, valid_bytes = parse_sram_read_data(elems[1:-1], array_h, array_w)

        # f: the reason why the ws_detail has higher sram read bytes with lower SRAM traces size
        # is because the valid bytes is more than the os
        valid_bytes = parse_sram_read_data(elems[1:])
        num_sram_read_bytes += valid_bytes
        # total_util += util
        # print("Total Util " + str(total_util) + ", util " + str(util))

    stop_clk = clk

    # f: detailed_str
    detailed_log += str(start_clk) + ",\t" + str(stop_clk) + ",\t" + str(num_sram_read_bytes) + ",\t"
    f.close()
    print('as this layer, the num sram of read bytes is {}'.format(num_sram_read_bytes))

    sram_clk = clk
    if clk > max_clk:
        max_clk = clk

    delta_clk = max_clk - min_clk

    sram_ofmap_bw = num_sram_ofmap_bytes / delta_clk
    sram_read_bw = num_sram_read_bytes / delta_clk
    # print("total_util: " + str(total_util) + ", sram_clk: " + str(sram_clk))
    # avg_util            = total_util / sram_clk * 100

    units = " Bytes/cycle"
    # print("Average utilization : \t"  + str(avg_util) + " %")
    # print("SRAM OFMAP Write BW, Min clk, Max clk")

    log = str(sram_read_bw) + ",\t" + str(sram_ofmap_bw) + ","
    # Anand: Enable the following line for debug
    # log += str(min_clk) + ",\t" + str(max_clk) + ","
    # print(log)
    # return log, avg_util
    return log, detailed_log


def test_get_bw_numbers(ifmap_sram_size=1,
                        filter_sram_size=1,
                        ofmap_sram_size=1,
                        data_flow='os',
                        topology_file='./topologies/yolo_v2.csv',
                        net_name='yolo_v2'):
    param_file = open(topology_file, 'r')

    detailed_log = "Layer," + \
                   "\tSRAM_read_start,\tSRAM_read_stop,\tSRAM_read_bytes," + \
                   "\tSRAM_write_start,\tSRAM_write_stop,\tSRAM_write_bytes,\n"

    fname = net_name + "_" + data_flow + "_avg_bw.csv"
    bw = open(fname, 'w')

    # just directly put on the source dir, no need to do clean (moving into folder) yet, we just wanna exam
    # whether the detail log is correct or not
    f4name = net_name + "_" + data_flow + "_detail.csv"
    detail = open(f4name, 'w')
    detail.write(detailed_log)

    first = True

    for row in param_file:
        if first:
            first = False
            continue

        elems = row.strip().split(',')
        # print(len(elems))

        # Do not continue if incomplete line
        if len(elems) < 9:
            continue

        name = elems[0]
        print("")
        print("Commencing run for " + name)

        ifmap_h = int(elems[1])
        ifmap_w = int(elems[2])

        filt_h = int(elems[3])
        filt_w = int(elems[4])

        num_channels = int(elems[5])

        # to solve ValueError: invalid literal for int() with base 10
        # eval to enable the math parsing. eval will do evaluation for all the strings, unsafe if the input is untrusted
        num_filters = int(eval(elems[6]))

        strides = int(elems[7])

        bw_log = str(ifmap_sram_size) + ",\t" + str(filter_sram_size) + ",\t" + str(
            ofmap_sram_size) + ",\t" + name + ",\t"
        max_bw_log = bw_log
        detailed_log = name + ",\t"

        bw_log = str(ifmap_sram_size) + ",\t" + str(filter_sram_size) + ",\t" + str(
            ofmap_sram_size) + ",\t" + name + ",\t"
        detailed_log = name + ",\t"

        print(net_name)

        if data_flow == 'os':
            bw_str, detailed_str = gen_bw_numbers(sram_read_trace_file="/home/zhongad/21_playground/SCALE-Sim-Fred"
                                                                       "/outputs"
                                                                       "/apr28_comb_os_effgrad_16x16_resnet18_forward"
                                                                       "/SRAM/resnet18_sram_read_"
                                                                       + name + ".csv",
                                                  sram_write_trace_file="/home/zhongad/21_playground/SCALE-Sim-Fred"
                                                                        "/outputs"
                                                                        "/apr28_comb_os_effgrad_16x16_resnet18_forward"
                                                                        "/SRAM/resnet18_sram_write_"
                                                                        + name + ".csv")
        elif data_flow == 'ws':
            bw_str, detailed_str = gen_bw_numbers(sram_read_trace_file="/home/zhongad/21_playground/SCALE-Sim-Fred"
                                                                       "/outputs"
                                                                       "/apr28_comb_ws_effgrad_16x16_resnet18_forward"
                                                                       "/SRAM/resnet18_sram_read_"
                                                                       + name + ".csv",
                                                  sram_write_trace_file="/home/zhongad/21_playground/SCALE-Sim-Fred"
                                                                        "/outputs"
                                                                        "/apr28_comb_ws_effgrad_16x16_resnet18_forward"
                                                                        "/SRAM/resnet18_sram_write_"
                                                                        + name + ".csv")
        else:
            raise ValueError('the given data flow {} is not supported to find SRAM traces'.format(data_flow))

        bw_log += bw_str
        bw.write(bw_log + "\n")

        detailed_log += detailed_str
        detail.write(detailed_log + "\n")


def main(args):
    forward_frame = pd.read_csv(args.forward_input_file)
    forward_sram_read_bytes = forward_frame['\tSRAM_read_bytes']
    forward_sram_write_bytes = forward_frame['\tSRAM_write_bytes']
    sum_forward_read = sum(forward_sram_read_bytes)
    sum_forward_write = sum(forward_sram_write_bytes)
    print('forward:')
    # /2, since the read part includes both ifmap and weight buffer offset on sram
    print('read bytes: {} \nwrite bytes: {}\n'.format(sum_forward_write/2, sum_forward_read))

    vani_frame = pd.read_csv(args.vani_backward_input_file)
    vani_sram_read_bytes = vani_frame['\tSRAM_read_bytes']
    vani_sram_write_bytes = vani_frame['\tSRAM_write_bytes']
    sum_vani_read = sum(vani_sram_read_bytes)
    sum_vani_write = sum(vani_sram_write_bytes)
    print('vani_backward:')
    # /2, since the read part includes both ifmap and weight buffer offset on sram
    print('read bytes: {} \nwrite bytes: {}\n'.format(sum_vani_write/2, sum_vani_read))

    effi_frame = pd.read_csv(args.forward_input_file)
    effi_sram_read_bytes = effi_frame['\tSRAM_read_bytes']
    effi_sram_write_bytes = effi_frame['\tSRAM_write_bytes']
    # print(effi_sram_read_bytes)
    layers_non_zero_grad_df = pd.read_csv('/home/zhongad/21_playground/SCALE-Sim-Fred/utils'
                                          '/effgrad_resnet18_non_zero_grad_df.csv')
    # print(layers_non_zero_grad_df)
    effi_sram_read_bytes *= layers_non_zero_grad_df['non_zero_grads_ratio']
    effi_sram_write_bytes *= layers_non_zero_grad_df['non_zero_grads_ratio']
    # print(effi_sram_read_bytes)
    sum_effi_read = sum(effi_sram_read_bytes)
    sum_effi_write = sum(effi_sram_write_bytes)
    print('effi_backward:')
    # /2, since the read part includes both ifmap and weight buffer offset on sram
    print('read bytes: {} \nwrite bytes: {}\n'.format(sum_effi_write/2, sum_effi_read))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='dissect the raw sram bytes info'
                                                 'into the read/write for forward,'
                                                 'vanilla backward, and effi backward')
    parser.add_argument('--forward_input_file', type=str, help='input csv details file',
                        default='/home/zhongad/21_playground/SCALE-Sim-Fred/outputs'
                                '/apr28_comb_os_effgrad_16x16_resnet18_forward/resnet18_detail.csv')
    parser.add_argument('--vani_backward_input_file', type=str, help='input csv details file',
                        default='/home/zhongad/21_playground/SCALE-Sim-Fred/outputs'
                                '/apr28_comb_os_effgrad_16x16_resnet18_vani_backward/resnet18_vani_backward_detail.csv')
    # parser.add_argument('--process_type', type=str, default='forward',
    #                     choices=['forward', 'vanilla_backward',
    #                              'effi_backward'])
    args = parser.parse_args()

    main(args)

# the following lines are for testing test_get_bw_numbers() and compare between ws and os, to see whether their r/w
# bytes in the output detail log

# os
# if __name__ == '__main__':
#     topology_file = '../topologies/conv_nets/resnet18_forward.csv'
#     test_get_bw_numbers(ifmap_sram_size=16384,  # these three sram sizes are from effigrad_forward.cfg
#                         filter_sram_size=8192,
#                         ofmap_sram_size=32768,
#                         topology_file=topology_file,
#                         data_flow='os',
#                         net_name=topology_file.split('/')[-1].split('.')[0])

# ws
# if __name__ == '__main__':
#     topology_file = '../topologies/conv_nets/resnet18_forward.csv'
#     test_get_bw_numbers(ifmap_sram_size=16384,  # these three sram sizes are from effigrad_forward.cfg
#                         filter_sram_size=8192,
#                         ofmap_sram_size=32768,
#                         topology_file=topology_file,
#                         data_flow='ws',
#                         net_name=topology_file.split('/')[-1].split('.')[0])
