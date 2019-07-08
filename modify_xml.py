#!usr/bin/python
# -*- coding: UTF-8 -*-
import sys
import os
import logging
from optparse import OptionParser

try:
    from Configparser import ConfigParser
except ImportError:
    from configparser import ConfigParser
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


class Modfiy_xml:

    def __init__(self,config,script_path,script_id_file_path,new_code_file_path):
        self.config = config
        self.script_path = script_path
        self.script_id_file = script_id_file_path

        self.success_script_list = []
        self.target_scripts_dict = self.scan_file(self.script_path)
        self.new_code_path = new_code_file_path

        try:
            self.add_update_mark = self.config.get("update-and-add","add_update_mark")
            self.above_mark = self.config.get("update-and-add","above_mark")
            self.below_mark = self.config.get("update-and-add","below_mark")
            self.replace_mark = self.config.get("replace","replace_mark")
            self.replace_old_code_mark = self.config.get("replace","replace_old_code_mark")
        except Exception as err:
            print(err)
            sys.exit(-1)

    def scan_file(self,src_path):
        try:
            case_dict = {}
            for root, folders, files in os.walk(src_path):
                for file in files:
                    if file.endswith(".xml"):
                        case_dict.update({file.replace(".xml","").lower():os.path.join(root,file).replace("\\","/")})
        except Exception as err:
            print(err)
        return case_dict

    def read_xml_resource(self):
        with open(self.new_code_path,"r") as f:
            code = [value.rstrip() for value in f.read().splitlines() if value != ""]

        _index = code.index(self.replace_mark)
        add_or_update_code = code[:_index]
        replace_code = code[_index:]
        if len(add_or_update_code) > 4 and len(replace_code) ==3:
            return_code = add_or_update_code
        elif len(add_or_update_code) == 4 and len(replace_code) >3:
            return_code = replace_code
        else:
            return_code = code
        return return_code

    def handle_new_code(self,code):
        """
        """
        sort_code ={}
        if self.add_update_mark in code and  self.replace_mark not in code:
            above_index = code.index(self.above_mark)
            below_index = code.index(self.below_mark)
            if len(code[:above_index]) > 1 and  len(code[below_index:]) == 1:
                sort_code.update({"mark":code[1:above_index]})
                sort_code.update({"code":code[above_index+2:below_index]})
            elif len(code[:above_index]) == 2 and len(code[below_index:])>1:
                sort_code.update({"mark":code[below_index+1:]})
                sort_code.update({"code":code[above_index +2:below_index]})
            else:
                sort_code.update({"above_mark":code[1:above_index]})
                sort_code.update({"below_mark":code[below_index+1:]})
                sort_code.update({"code":code[above_index +2:below_index]})
        elif self.add_update_mark not in code and self.replace_mark in code:
            above_index = code.index(self.replace_old_code_mark)
            sort_code.update({"replace_mark":code[1:above_index]})
            sort_code.update({"code":code[above_index+2:]})
        elif self.add_update_mark in code and  self.replace_mark in code:
            # above_index = code.index(self.above_mark)
            # below_index = code.index(self.below_mark)
            # replace_index = code.index(self.replace_mark)
            # replace_above_index = code.index(self.replace_old_code_mark)
            pass

        else:
            logging.error("ERROR: Please input correct code!")
            print ("ERROR: Please input correct code!")

        return sort_code

    def contrast_code(self,script_content,new_code):
        """
        """
        index_list = []
        change_code = []
        script_length = len(script_content)

        if "replace_mark" in new_code:
            mark = new_code["replace_mark"]
            change_code = new_code["code"]
            mark_length = len(mark)
            new_mark = [code.strip() for code in mark]
            fuzzy_mark_list = []
            for mark_code in new_mark:
                fuzzy_list = self.fuzzy_match_one(mark_code,script_content)
                fuzzy_mark_list.append(fuzzy_list)
            if None not in fuzzy_mark_list:
                index_list = self.parse_index(fuzzy_mark_list,script_content,new_mark,mark_length,script_length)
        elif self.add_update_mark in new_code:
            pass
        else:
            pass

        return index_list,change_code

    def parse_index(self,fuzzy_list,script_content,mark,mark_length,script_length):
        """
        """
        begin_index = 0
        end_index = 0
        best_res = fuzzy_list[0][0]
        best_num = script_content.count(best_res)
        index_list = []
        if best_num == 1:
            begin_index = script_content.index(best_res)
            vir_end_index = begin_index + mark_length
            script_begin = begin_index + 1
            # print(mark_length,script_length,begin_index,vir_end_index)
            if vir_end_index >= script_length:
                return [[0,0]]
            if mark_length == 1:
                return [[begin_index,vir_end_index]]
            else:
                if script_content[vir_end_index] == mark[mark_length-1] and script_content[vir_end_index-1] == mark[mark_length-2]:
                    end_index = vir_end_index  
                else:
                    num_list = []
                    for i in range(1,mark_length):
                        if mark[i].startswith("<!--"):
                            continue
                        else:
                            for j in range(script_begin,script_length):
                                if script_content[j].startswith("<!--"):
                                    continue
                                else:
                                    if fuzz.ratio(script_content[j],mark[i]) >= 95:
                                        num_list.append(j)
                                        script_begin = j + 1
                                        break
                                    else:
                                        return [[0,0]]
                    end_index = num_list[-1] + 1
                index_list.append([begin_index,end_index])
        else:
            best_num_list = []
            a = 0
            for i in range(best_num):
                num = script_content.index(best_res,a)
                best_num_list.append(num)
                a = num + 1
            for num in best_num_list[::-1]:
                begin_index = num
                vir_end_index = begin_index + mark_length
                script_begin = begin_index + 1
                # print(mark_length,script_length,begin_index,vir_end_index)
                if vir_end_index >= script_length:
                    return [[0,0]]
                if mark_length == 1:
                    index_list.append([begin_index,vir_end_index])
                else:
                    if script_content[vir_end_index] == mark[mark_length-1] and script_content[vir_end_index-1] == mark[mark_length-2]:
                        end_index = vir_end_index
                    else:
                        num_list = []
                        for i in range(1,mark_length):
                            if mark[i].startswith("<!--"):
                                continue
                            else:
                                for j in range(script_begin,script_length):
                                    if script_content[j].startswith("<!--"):
                                        continue
                                    else:
                                        if fuzz.ratio(script_content[j],mark[i]) >= 95:
                                            num_list.append(j)
                                            script_begin = j + 1
                                            break
                                        else:
                                            return [[0,0]]
                        end_index = num_list[-1] + 1
                    index_list.append([begin_index,end_index])
        return index_list

    def fuzzy_match_one(self,mark_code,script_content):

        logging.info("matching: " + mark_code)
        print ("matching: " + mark_code)
        result = process.extractOne(mark_code,script_content,scorer = fuzz.ratio)
        logging.info(result)
        print (">>>" + result)

        return result

    def space_count(self,code):
        num = 0
        for i in code:
            if i.isspace():
                num += 1
            else:
                break
        return num

    def modify_script(self,case_path,new_code):

        case_number = 0
        with open(case_path,"r") as f:
            content_list = [val for val in f.read().splitlines() if val != ""]
        content_list_stript = [value.strip() for value in content_list if value != ""]

        index_list,change_code= self.contrast_code(content_list_stript,self.handle_new_code(new_code))
        logging.info("section_index:" + str(index_list))
        for index in index_list:
            print("section_index:" + str(index))
            begin_index = index[0]
            end_index = index[1]
            if begin_index == end_index == 0:
                logging.info("-------------------------------can't found the mark code.")
                print("-------------------------------can't found the mark code.")
            else:
                num = self.space_count(content_list[begin_index])
                xml_new = [" " * int(num) + val for val in change_code]
                content_list[begin_index:end_index] = xml_new
                with open(case_path,"w") as f:
                    for val in content_list:
                        f.write(val + "\n")
                case_number = 1
                logging.info("------------------------------successful")
                print("------------------------------successful")
        return case_number

    def run(self):

        num = 0
        with open(self.script_id_file,"r") as f:
            script_list = [val for val in f.read().splitlines() if val != ""]
        for script in script_list:
            script_name = script.replace(".xml","").lower()
            if script_name in self.target_scripts_dict:
                logging.info("-------------------------Begin modify {}".format(script))
                print ("-------------------------Begin modify {}".format(script))
                try:
                    return_num = self.modify_script(self.target_scripts_dict[script_name],self.read_xml_resource())
                    if return_num == 1:
                        self.success_script_list.append(script)
                        num += return_num
                except Exception as err:
                    logging.error(err)
                    print(err)
            else:
                logging.error("Can't find {} in this production line!".format(script))
                print ("Warning：Can't find {} in this production line!".format(script))

        print("successful case id:")
        with open("./success_scripts_list.txt","w") as f:
            for case in self.success_script_list:
                print(case)
                f.write(case + "\n")
        print("--------------------Total: " + str(num) + "\n")  



if __name__ == '__main__':


    config = ConfigParser()
    current_path = os.path.split(os.path.realpath(sys.argv[0]))[0].replace("\\","/")
    if not (os.path.join(current_path, 'modfiy_xml_config.ini')):
        print('modfiy_xml_config.ini is not exist')
        sys.exit(-1)
    try:
        config.read(os.path.join(current_path, 'modfiy_xml_config.ini'))
    except Exception as e:
        print(e)
        sys.exit(-1)

    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s | %(levelname)s %(message)s",
                        datefmt="%a, %d %b %y %H:%M:%S",
                        filename=current_path + os.sep + "result.log")

    parser = OptionParser('usage: %prog [options]')
    parser.add_option('-r', '--root_path', dest='root_path', default=None,
                      help='the root path to search scripts, must set')
    parser.add_option('-c', '--cases_list_file', dest='cases_list_file', default=None,
                      help='the file contains the cases list to modfiy,must set' )
    parser.add_option('-n', '--new_code_file', dest='new_code_file', default=None,
                      help='the file contains old code and new code, must set')

    (options, args) = parser.parse_args()
    Modfiy_xml(config,options.root_path, options.cases_list_file, options.new_code_file).run()