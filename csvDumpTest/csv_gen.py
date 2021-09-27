import re
import csv
import argparse

# this csv generator parse the dramsim3 output and dump csv results

def main():
    parser = argparse.ArgumentParser(description="Parsing the grep output of dramsim3 result, and dumping csv")
    parser.add_argument('--value_name', type=str, choices=['total_energy', 'average_power'], default='total_energy')
    parser.add_argument('--workload_type_name', type=str, choices=['filter_read', 'ifmap_read', 'ofmap_write'], default='filter_read')
    parser.add_argument('--input-txt,', type=str, dest='input')
    parser.add_argument('--output-csv', type=str, dest='output')

    args = parser.parse_args()
    csv_generator(value_name=args.value_name,
                  workload_type_name=args.workload_type_name,
                  input_txt=args.input,
                  output_csv=args.output)

def csv_generator(value_name='total_energy',
                  workload_type_name='filter_read',
                  input_txt="test_sample.txt", output_csv="outfile_ult.csv"):
    with open(input_txt) as infile, open(output_csv, "w") as outfile:
        data = infile.read()  # Read infile content
        layer_value = []
        if value_name == 'average_power':
            layer_list = re.findall(r"" + workload_type_name + '_(.*?).txt:75:average_power',
                                         data)
            for i in range(len(layer_list)):
                layer_value += re.findall(
                    r"" + workload_type_name + "_" + str(layer_list[i]) +
                    ".txt:75:average_power                  =      (.*?)   #",
                    data)
        elif value_name == 'total_energy':
            layer_list = re.findall(r"" + workload_type_name + '_(.*?).txt:78:total_energy',
                                    data)
            for i in range(len(layer_list)):
                layer_value += re.findall(
                    r"" + workload_type_name + "_" + str(layer_list[i]) +
                    ".txt:78:total_energy                   =  (.*?)   #",
                    data)
        else:
            raise Exception("ABORT: value_name {} is not supported".format(value_name))
        writer = csv.writer(outfile)
        writer.writerow(['layer_type', value_name])  # Write Header
        for i in range(len(layer_value)):
            writer.writerow([layer_list[i], layer_value[i]])

        print('layer_list is {}'.format(layer_list))
        print('layer_value is {}'.format(layer_value))


if __name__ == "__main__":
    # main()
    # csv_generator('total_energy')
    csv_generator('average_power')
