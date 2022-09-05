import csv, re, os

header = ['100_ActualLoad', '100_ssj_ops', '100_AvgPower', '100_PerfPowerRatio',
'90_ActualLoad', '90_ssj_ops', '90_AvgPower', '90_PerfPowerRatio',
'80_ActualLoad', '80_ssj_ops', '80_AvgPower', '80_PerfPowerRatio',
'70_ActualLoad', '70_ssj_ops', '70_AvgPower', '70_PerfPowerRatio',
'60_ActualLoad', '60_ssj_ops', '60_AvgPower', '60_PerfPowerRatio',
'50_ActualLoad', '50_ssj_ops', '50_AvgPower', '50_PerfPowerRatio',
'40_ActualLoad', '40_ssj_ops', '40_AvgPower', '40_PerfPowerRatio',
'30_ActualLoad', '30_ssj_ops', '30_AvgPower', '30_PerfPowerRatio',
'20_ActualLoad', '20_ssj_ops', '20_AvgPower', '20_PerfPowerRatio',
'10_ActualLoad', '10_ssj_ops', '10_AvgPower', '10_PerfPowerRatio',
'ActiveIdle', 'HW_Vendor', 'HW_Model', 'HW_FormFactor', 'HW_CPUName', 
'HW_CPUChars', 'HW_CPUFreq', 'HW_CPUsEnabled','HW_HardwareThreads', 
'HW_CPUsOrderable', 'HW_PrimaryCache', 'HW_SecondaryCache','HW_TertiaryCache',
'HW_OtherCache', 'HW_MemAmountGB','HW_DIMMNumAndSize','HW_MemDetails', 
'HW_PSUQuantAndRating', 'HW_PSUDetails','HW_DiskDrive','HW_DiskController',
'HW_NICSNumAndType', 'HW_NICSFirm/OS/Conn','HW_NetSpeedMbit','HW_Keyboard','HW_Mouse',
'HW_Monitor', 
'HW_OpticalDrive', 'HW_Other', 'SW_PowerManagement', 'SW_OS', 'SW_OSVersion', 
'SW_Filesystem', 'SW_JVMVendor', 'SW_JVMVersion', 'SW_JVMCLIOpts', 
'SW_JVMAffinity', 'SW_JVMInstances', 'SW_JVMInitialHeapMB', 'SW_JVMMaxHeapMB', 
'SW_JVMAddressBits', 'SW_BootFirmwareVersion', 'SW_MgmtFirmwareVersion', 
'SW_WorkloadVersion', 'SW_DirectorLocation', 'SW_Others', 
]

rows = []
rowcount=-1

for f in os.scandir('../raw/html/'):
    if f.is_file():
        rowcount+=1
        rows.append([])
        o = open(f,'r')
        text = o.read()
        o.close()

        ## Get Power Chart
        for x in range(100, 0, -10):
            m = re.search(f'<td>{x}%</td>$'
                '\s*<td>(.*)%</td>$'
                '\s*<td>(.*)</td>$'
                '\s*<td>(.*)</td>$'
                '\s*<td>(.*)</td>$'
                , text, re.M)
            if m:
                ssj_ops_cln = re.sub(',', "", m.group(2))
                avg_pwr_cln = re.sub(',', "", m.group(3))
                perf_pwr_ratio_cln = re.sub(',', "", m.group(4))
                rows[rowcount].extend([m.group(1), ssj_ops_cln, avg_pwr_cln
                    , perf_pwr_ratio_cln])
                #print(f"Actual Load: {m.group(1)} --- ssj_ops: {m.group(2)} --- avg.power: {m.group(3)} --- perf.power.ratio: {m.group(4)}\n")
        
        ## Get Idle Power
        m = re.search('Active Idle.*$'
            '\s*<td>.*</td>$'
            '\s*<td>(.*)</td>$'
            , text, re.M)
        if m: rows[rowcount].append(m.group(1))

        ## Get Hardware Info
        m = re.search('Hardware Vendor:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'   # 1 
            '\s*.*Model:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'                  # 2   
            '\s*.*Form Factor:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'            # 3
            '\s*.*CPU Name:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'               # 4
            '\s*.*CPU Characteristics:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'    # 5
            '\s*.*CPU Frequency \(MHz\):</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'  # 6
            '\s*.*CPU\(s\) Enabled:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'       # 7
            '\s*.*Hardware Threads:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'       # 8
            '\s*.*CPU\(s\) Orderable:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'     # 9
            '\s*.*Primary Cache:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'          # 10
            '\s*.*Secondary Cache:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'        # 11
            '\s*.*Tertiary Cache:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'         # 12
            '\s*.*Other Cache:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'            # 13
            '\s*.*Memory Amount \(GB\):</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'   # 14 
            '\s*.*# and size of DIMM:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'     # 15
            '\s*.*Memory Details:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'         # 16
            '\s*.*Power Supply Quantity and Rating \(W\):</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' #17
            '\s*.*Power Supply Details:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'   # 18
            '\s*.*Disk Drive:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'             # 19
            '\s*.*Disk Controller:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'        # 20
            '\s*.*# and type of Network Interface Cards \(NICs\) Installed:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' # 21
            '\s*.*NICs Enabled in Firmware / OS / Connected:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' # 22
            '\s*.*Network Speed \(Mbit\):</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' # 23
            '\s*.*Keyboard:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'               # 24
            '\s*.*Mouse:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'                  # 25
            '\s*.*Monitor:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'                # 26
            '\s*.*Optical Drives:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'         # 27
            '\s*.*Other Hardware:</a></td>$\s*.*>(.*)</td>'                          # 28
            ,text , re.M)

        if m: #print(m.group(28))
            for x in range(1,29):
                rows[rowcount].append(m.group(x))

        ## Get Software Info
        m = re.search('Power Management:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'  # 1
            '\s*.*Operating System \(OS\):</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' # 2   
            '\s*.*OS Version:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'             # 3   
            '\s*.*Filesystem:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'             # 4   
            '\s*.*JVM Vendor:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'             # 5   
            '\s*.*JVM Version:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'            # 6   
            '\s*.*JVM Command-line Options:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' # 7   
            '\s*.*JVM Affinity:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'           # 8
            '\s*.*JVM Instances:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'          # 9
            '\s*.*JVM Initial Heap \(MB\):</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' # 10
            '\s*.*JVM Maximum Heap \(MB\):</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' # 11
            '\s*.*JVM Address Bits:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'       # 12
            '\s*.*Boot Firmware Version:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'  # 13
            '\s*.*Management Firmware Version:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' # 14
            '\s*.*Workload Version:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'       # 15
            '\s*.*Director Location:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'      # 16
            '\s*.*Other Software:</a></td>$\s*.*>(.*)</td>'                          # 17
            ,text , re.M)

        if m: #print(m.group(17))
            for x in range(1, 18):
                rows[rowcount].append(m.group(x))


#print(rows)
with open('spec_data.csv', 'w', encoding='UTF8', newline='') as f:
    writer = csv.writer(f, delimiter='|')
    writer.writerow(header)
    writer.writerows(rows)
