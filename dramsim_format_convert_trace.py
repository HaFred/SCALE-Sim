import math
import tqdm
from dram_trace import prune
import os
'''
Mod on Apr13:
    Tyring to make the dram output trace with positive clock cycle, thus a temp_offset is needed for each trace file at
    very beginning. 
'''
# dramsim3 format dram_read_trace output fn
def dram_trace_read_dramsim(
        sram_sz=512 * 1024,  # word size
        word_sz_bytes=1,
        min_addr=0, max_addr=1000000,
        default_read_bw=4,  # default is arbitrary; f: this bw is how much word read per cycle
        sram_trace_file="sram_log.csv",
        dram_trace_file="dram_log.csv",
        verbose=False
):
    t_fill_start = -1
    t_drain_start = 0
    init_bw = default_read_bw

    sram = set()  # the python set() built on hashmap, which returns the smallest int for hashmap. So not random
    # for the int in the set(); however the set.pop for integer ele in set, will always in a increasing order
    sram_requests = open(sram_trace_file, 'r')
    dram_traces = open(dram_trace_file, 'w')
    offset = 0

    for entry in sram_requests:
        elems = entry.strip().split(',')
        elems = prune(elems)
        elems = [float(x) for x in elems]

        clk = elems[0]

        for e in range(1, len(elems)):
            if (elems[e] not in sram) and (elems[e] >= min_addr) and (elems[e] <= max_addr):
                # add the new element to sram
                sram.add(elems[e])

                # used up all the unique data in the SRAM
                # f: highly doubt that, the original version is typo here
                if len(sram) * word_sz_bytes > sram_sz:

                    # update t_fill_start
                    if t_fill_start == -1:
                        t_fill_start = t_drain_start - math.ceil(len(sram) / (init_bw * word_sz_bytes))

                    # generate the filling trace from time t_fill_start to t_drain_start
                    cycles_needed = t_drain_start - t_fill_start
                    words_per_cycle = math.ceil(len(sram) / (cycles_needed * word_sz_bytes))
                    c = t_fill_start

                    # if dram_traces file is empty, make the t_fill_start+1 as the offset
                    if (os.stat(dram_trace_file).st_size == 0) and (t_fill_start != -1):
                        offset = t_fill_start
                        # input("Release offset= {}, press to continue".format(offset))

                    if verbose:
                        dram_traces.write('#t_fill_start={}, len(sram)={}\n'.format(t_fill_start, len(sram)))
                        print("Word per cycle = " + str(words_per_cycle))
                    while len(sram) > 0:
                        for _ in range(words_per_cycle):
                            if len(sram) > 0:
                                p = sram.pop()

                                # the dramsim format trace
                                # print('for loop, offset is {}, t_fill_start is {}'.format(offset, t_fill_start))
                                trace = "{} {} {}".format(hex(int(p)), "READ", int(c-offset+1))
                                trace += "\n"
                                dram_traces.write(trace)
                        c += 1
                    t_fill_start = t_drain_start
                    t_drain_start = clk

    if len(sram) > 0:
        if t_fill_start == -1:
            t_fill_start = t_drain_start - math.ceil(len(sram) / (init_bw * word_sz_bytes))

        # generate the filling trace from t_filling_start to t_drain_start
        cycles_needed = t_drain_start - t_fill_start
        words_per_cycle = math.ceil(len(sram) / (cycles_needed * word_sz_bytes))
        c = t_fill_start

        # generate the filling trace from time t_fill_start to t_drain_start
        # fixme either into if loop or for loop, this is a workaround now, figure out why and how better
        if (os.stat(dram_trace_file).st_size == 0) and (t_fill_start != -1):
            offset = t_fill_start

        if verbose:
            dram_traces.write('# len(sram)>0, t_fill_start={}, len(sram)={}\n'.format(t_fill_start, len(sram)))
        while len(sram) > 0:
            if verbose:
                print("for current c={}, len(sram)={}".format(c, len(sram)))
            for _ in range(words_per_cycle):
                if len(sram) > 0:
                    p = sram.pop()
                    # print('if loop, offset is {}'.format(offset))
                    trace = "{} {} {}".format(hex(int(p)), "READ", int(c-offset+1))
                    trace += "\n"
                    dram_traces.write(trace)
            c += 1
    sram_requests.close()
    dram_traces.close()


# write fn
# fixme why there exists filling and draining sram buffer, but not for read dram fn?
# seems like double buffer, one for fill, another drain, but is it? why not read_dram?
# Write no min/max addr, coz only needs to write into ofmap, no ifmap/filter needed
def dram_trace_write_dramsim(
        ofmap_sram_size=1 * 1024,  # word size
        data_width_bytes=1,
        default_write_bw=4,
        sram_write_trace_file="sram_write.csv",
        dram_write_trace_file="dram_write.csv",
        verbose=False
):
    sram_requests = open(sram_write_trace_file, 'r')
    dram_traces = open(dram_write_trace_file, 'w')
    last_clk = 0
    clk = 0
    sram_buffer = [set(), set()]  # filling_buffer & draining_buffer
    filling_buf = 0
    draining_buf = 1

    for row in sram_requests:
        elems = row.strip().split(',')
        elems = prune(elems)
        elems = [float(x) for x in elems]

        clk = elems[0]

        # if enough space is in the filling buffer
        # keep filling the buffer
        if (len(sram_buffer[filling_buf]) + (len(elems) - 1) * data_width_bytes) < ofmap_sram_size:
            for i in range(1, len(elems)):
                sram_buffer[filling_buf].add(elems[i])

        # filling buffer is full, spill the data to the other buffer
        else:
            # if there is data in the draining buffer
            # drain it
            if verbose:
                print("Draining data. CLK = " + str(clk))
            if len(sram_buffer[draining_buf]) > 0:
                delta_clks = clk - last_clk
                data_per_clk = math.ceil(len(sram_buffer[draining_buf]) / delta_clks)
                if verbose:
                    print("Data per clk = " + str(data_per_clk))

                # Drain the data
                c = last_clk + 1
                while len(sram_buffer[draining_buf]) > 0:
                    # trace = str(c) + ", "
                    c += 1
                    for _ in range(int(data_per_clk)):
                        if len(sram_buffer[draining_buf]) > 0:
                            addr = sram_buffer[draining_buf].pop()
                            trace = "{} {} {}".format(hex(int(addr)), 'WRITE', int(c))
                            # trace += str(addr) + ", "
                            dram_traces.write(trace + "\n")

            # Swap the ids for drain buffer and fill buffer
            tmp = draining_buf
            draining_buf = filling_buf
            filling_buf = tmp

            # Set the last clk value
            last_clk = clk

            # Fill the new data now
            for i in range(1, len(elems)):
                sram_buffer[filling_buf].add(elems[i])

    # drain the last draining buffer
    reasonable_clk = clk
    if len(sram_buffer[draining_buf]) > 0:
        data_per_clk = default_write_bw

        # drain the data
        c = last_clk + 1
        while len(sram_buffer[draining_buf]) > 0:
            c += 1
            for _ in range(int(data_per_clk)):
                if len(sram_buffer[draining_buf]) > 0:
                    addr = sram_buffer[draining_buf].pop()
                    trace = "{} {} {}".format(hex(int(addr)), 'WRITE', int(c))
                    dram_traces.write(trace + "\n")
            reasonable_clk = max(c, clk)

    # drain the last filled buffer
    if len(sram_buffer[filling_buf]) > 0:
        data_per_clk = default_write_bw

        # drain the data
        c = reasonable_clk + 1
        while len(sram_buffer[filling_buf]) > 0:
            c += 1
            for _ in range(int(data_per_clk)):
                if len(sram_buffer[filling_buf]) > 0:
                    addr = sram_buffer[filling_buf].pop()
                    trace = "{} {} {}".format(hex(int(addr)), 'WRITE', int(c))
                    dram_traces.write(trace + "\n")

    # all done
    sram_requests.close()
    dram_traces.close()

if __name__ == "__main__":

    # dram write 64 vs. 1024
    # dram_trace_write_dramsim(ofmap_sram_size=64,
    #                          sram_write_trace_file='./outputs/effgrad_16x16_ws_resnet18_good_nameFormat/sram/resnet18_sram_write_FC6.csv',
    #                          dram_write_trace_file='./outputs/test_dram_write_output.csv',
    #                          verbose=True)

    # test for filter dram read
    dram_trace_read_dramsim(sram_sz=8192,
                            word_sz_bytes=1,
                            min_addr=1e6, max_addr=2e6,
                            sram_trace_file='./outputs/effgrad_16x16_ws_resnet18_good_nameFormat/sram/resnet18_sram_read_Conv1.csv',
                            dram_trace_file='./outputs/test_dram_read_output.csv',
                            verbose=False)
