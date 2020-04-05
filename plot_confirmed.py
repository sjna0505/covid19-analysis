#!/usr/bin/python
import time
import getopt, sys
import os

def gnu_dem(xsize,ysize,ifile,ofile,countries):
    country_line = []
    for i, each_country in enumerate(sorted(countries.keys())):
        country_line.append("\"%s\" using %d:%d w lines title '%s'" % (ifile,2*i+1,2*i+2,each_country))
    return '''
set terminal png size %d,%d
set output "%s"
set logscale xy
plot %s
''' % (xsize,ysize,ofile,",".join(country_line))
     
def read_confirmed(csv_file,countries):
    f = open(csv_file)
    max_data = 0
    if f:
        data = f.read().split("\n")
        cpos = None
        spos = None
        dpos = None
        have_sum_countries = set({})
        sum_country = {}
        for i, each_data in enumerate(data):
            if i == 0:
                head = each_data.split(",")
                for j, head_field in enumerate(head):
                    if cpos == None and 'COUNTRY' in head_field.upper():
                        cpos = j
                    if spos == None and 'STATE' in head_field.upper():
                        spos = j
                    if dpos == None and get_epoch(head_field)!= None:
                        dpos = j
                if cpos == None or spos == None or dpos == None:
                    print "%s csv file format is not right" % csv_file
                    return 0
            else:
                if '"' in each_data:
                    each_row = handle_comma(each_data.split(","))
                else:
                    each_row = each_data.split(",")
                if len(each_row) < dpos: continue

                country = each_row[cpos].upper()
                if country not in countries:
                    continue
                if len(each_row[spos]) == 0:
                    try:
                        countries[country] = get_delta_pair(map(lambda x: int(x),each_row[dpos:]))
                        if len(countries[country]) > max_data:
                            max_data = len(countries[country])
                    except Exception as err:
                        print "%s doesn't have correct format data. %s" % (country, str(err))
                        continue
                    have_sum_countries.add(country)
                else:
                    if not country in sum_country:
                        try:
                            sum_country[country] = map(lambda x: int(x),each_row[dpos:])
                        except Exception as err:
                            print "%s doesn't have correct format data. %s" % (country, str(err))
                            continue
                    else:
                        for j, value in enumerate(each_row):
                            if j < dpos : continue
                            index = j - dpos
                            if index < len(sum_country[country]):
                                try:
                                    sum_country[country][index] += int(value)
                                except Exception as err:
                                    print "%s doesn't have correct format data. %s" % (country, str(err))
                                    continue
        f.close()
        for country in sum_country.keys():
            if not country in have_sum_countries:
                countries[country] = get_delta_pair(sum_country[country])
                if len(countries[country]) > max_data:
                    max_data = len(countries[country])

    else:
        print "file %s not found" % csv_file
        return 0
    return max_data
def handle_comma(A):
    B = []
    prev = ""
    for each_a in A:
        if '"' in each_a:
            if prev == "" and '"' == each_a[0]:
                prev = each_a[1:]
            if prev != "" and '"' == each_a[-1]:
                B.append(prev +","+each_a[:len(each_a)-1])
        else:
            B.append(each_a)
    return B

def get_delta_pair(A):
    B = []
    initialized = False
    for each_a in A: 
        prev = len(B) - 1
        if prev >= 0:
            delta = each_a - B[prev][0]
            if delta > 0 and each_a > 0: 
                if B[prev][1] == 0:
                    B.pop()
                B.append((each_a,delta)) 
        else:
            if each_a > 0: 
                if initialized:
                    B.append((each_a,each_a)) 
                else:
                    initialized = True
                    B.append((each_a,0)) 
            else:
                initialized = True
    return B

def write_pair(ifile,date_num,countries):
    f = open(ifile,"w")
    if f:
        key_country = {}
        for i in xrange(0,date_num):
            each_row = []
            for each_country in sorted(countries.keys()):
                if i < len(countries[each_country]):
                    each_row.append("%d\t%d" % (countries[each_country][i][0],countries[each_country][i][1]))
                else:
                    each_row.append("%d\t%d" % (countries[each_country][-1][0],countries[each_country][-1][1]))

            f.write("\t".join(each_row)+"\n")
        f.close()
        return True
    else:
        print "can't create %s" % ifile
        return False

def get_epoch(date_string):
    try:
        return int(time.mktime(time.strptime(date_string,"%m/%d/%y")))
    except:
        return None

def usage():
    print '''plot_confirmed.py [options] time_series_covid19_confirmed_global.csv
    -h this help
    -o output png default is 'covid19.png'
    -x x size of png default is 600
    -y y size of png default is 400
    -c interested countres to add. the list should be separated by "|" and should be quoted by "", 
        default countries are 'Korea, South','United Kingdom','US','Italy','China','France','Spain','Germany','Japan'
        ex: "Russia|Thailand|Philippines|Brazil"
'''
def main():
    try: 
        opts, args = getopt.getopt(sys.argv[1:],"ho:x:y:c:")
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(0)
    if not args or '-h' in opts:
        usage()
        sys.exit(0)

    csv_file = args[0]

    ofile = 'covid19.png'
    xsize = 600
    ysize = 400
    interested_countries = set(['Korea, South','United Kingdom','US','Italy','China','France','Spain','Germany','Japan'])

    for opt, value in opts:
        if opt == '-x':
            try:
                xsize = int(value)
            except:
                pass
        if opt == '-y':
            try:
                ysize = int(value)
            except:
                pass
        if opt == '-c':
            interested_countries.update(value.split("|"))
        if opt == '-o':
            ofile = value

    countries = {}
    for each_country in interested_countries:
        countries[each_country.upper()] = []

    date_num = read_confirmed(csv_file,countries)

    if date_num == 0:
        print "no data to plot"
        sys.exit(1)

    for each_country in countries: 
        if len(countries[each_country]) == 0:
            del countries[each_country]

    write_pair('to_plot.txt',date_num,countries)
    f = open('to_plot.dem',"w")
    if f:
        f.write(gnu_dem(xsize,ysize,'to_plot.txt',ofile,countries))
        f.close()
        os.system("gnuplot to_plot.dem")
    else:
        print "can't create to_plot.dem"
        sys.exit(1)

if __name__=='__main__':
    main()
