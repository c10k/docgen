#!/usr/bin/env python3

import argparse
from os.path import basename, splitext, isdir, abspath, join, isfile
from os import getcwd, remove


class comments:
    def __init__(self, comment_lines):
        self.comment_lines = []
        for each_line in comment_lines:
            each_line = each_line.strip('*/ \t\n')
            if each_line:
                self.comment_lines.append(each_line)

    def get_properties(self):
        '''
        Process the comments and retrieve info from them.
        FOR NOW ONLY FUNCTIONS, METHODS OR CTORS WILL BE PARSED.
        '''
        temp = ''.join(self.comment_lines).split('@')
        comment_start = temp[1].split(' ')[0]
        if comment_start != "method" and comment_start != "function" and comment_start != "construct":
            return False
        else:
            properties = dict({
                'desc': None,
                'is_what': None,
                'access': None,
                'name': None,
                'params': [],
                'returns': [],
                'throws': []
            })
            for each_line in temp:
                if each_line:
                    line_tag = "Line -> " + each_line
                    try:
                        if each_line.startswith(
                                "method") or each_line.startswith(
                                    "func") or each_line.startswith(
                                        "construct"):
                            if properties['is_what'] is None:
                                is_what, name = each_line.split(' ')
                                properties['is_what'] = is_what
                                properties['name'] = name
                            else:
                                raise Exception(
                                    "Invalid comment.. @func or @method or @construct tag found again in a single comment",
                                    line_tag)
                        elif each_line.startswith("access"):
                            if properties['access'] is None:
                                parsed_access = each_line.split(' ')
                                if len(parsed_access) == 2:
                                    properties['access'] = parsed_access[1]
                                else:
                                    raise Exception(
                                        "Invalid comment.. access val not specified with @access tag",
                                        line_tag)
                            else:
                                raise Exception(
                                    "Invalid comment.. @access tag found again in a single comment",
                                    line_tag)
                        elif each_line.startswith("desc"):
                            if properties['desc'] is None:
                                firstSpacePos = each_line.find(' ')
                                desc = each_line[firstSpacePos + 1:]
                                properties['desc'] = desc
                            else:
                                raise Exception(
                                    "Invalid comment.. @desc tag found again in a single comment",
                                    line_tag)
                        elif each_line.startswith("param"):
                            openParenPos = each_line.find('{')
                            closeParenPos = each_line.find('}')
                            if openParenPos < 0 or closeParenPos < 0:
                                raise Exception(
                                    "Invalid comment.. @param '{' or '}' missing",
                                    line_tag)
                            else:
                                parsed_param = []
                                type_name = each_line[openParenPos + 1:
                                                      closeParenPos]
                                parsed_param.append(type_name)
                                name_and_desc = each_line[
                                    closeParenPos + 2:].split(' ', 1)
                                if len(name_and_desc) != 2:
                                    raise Exception(
                                        "Invalid comment.. @param tag takes 3 values",
                                        line_tag)
                                else:
                                    parsed_param.extend(name_and_desc)
                                    parsed_param[0], parsed_param[
                                        1] = parsed_param[1], parsed_param[0]
                                    properties['params'].append(parsed_param)
                        elif each_line.startswith("returns"):
                            openParenPos = each_line.find('{')
                            closeParenPos = each_line.find('}')
                            if openParenPos < 0 or closeParenPos < 0:
                                raise Exception(
                                    "Invalid comment.. @returns '{' or '}' missing",
                                    line_tag)
                            else:
                                parsed_ret = []
                                type_name = each_line[openParenPos + 1:
                                                      closeParenPos]
                                parsed_ret.append(type_name)
                                desc = each_line[closeParenPos + 2:]
                                parsed_ret.append(desc)
                                properties['returns'].append(parsed_ret)
                        else:
                            raise Exception(
                                "Invalid comment.. Line starting with unknown tag found",
                                line_tag)
                    except Exception:
                        raise Exception(line_tag)
            return properties

    def __str__(self):
        COMMENT_TAG = "=" * 10 + "COMMENT" + "=" * 10 + '\n'
        return COMMENT_TAG + '\n'.join(self.comment_lines)


class code:
    def __init__(self, code_lines):
        self.code_lines = ''.join(code_lines)

    def get_properties(self):
        '''
        Process the code and retrieve info from them.
        FOR NOW THIS ONLY RETURNS THE PROTOTYPE OF FUNCS, METHS, CTORS.
        '''
        firstParenPos = self.code_lines.find('{')
        firstSemiColPos = self.code_lines.find(';')
        if firstParenPos > 0 and firstSemiColPos > 0:
            firstEncountered = min(firstParenPos, firstSemiColPos)
        elif firstParenPos > 0 and firstSemiColPos < 0:
            firstEncountered = firstParenPos
        elif firstParenPos < 0 and firstSemiColPos > 0:
            firstEncountered = firstSemiColPos
        else:
            raise Exception(
                "Invalid code.. No ';' or '{' encountered while extracting function prototype, ",
                self.code_lines)
        return self.code_lines[:firstEncountered]

    def __str__(self):
        CODE_TAG = "." * 10 + "CODE" + "." * 10 + '\n'
        return CODE_TAG + self.code_lines


class segment:
    def __new__(segment, comment_lines, code_lines, file_name, dest_dir):
        # This __new__ method only allows object creation if comm.getproperties
        # does not return False i.e. the segment object will only be constructed
        # if segment is of function/method/constructor.
        temp_comm = comments(comment_lines)
        res = temp_comm.get_properties()
        if res is not False:
            return object.__new__(segment)
        else:
            return None

    def __init__(self, comment_lines, code_lines, file_name, dest_dir):
        self.__comm = comments(comment_lines)
        self.__code = code(code_lines)
        self.__file_name = join(dest_dir,
                                splitext(basename(file_name))[0] + ".md")
        try:
            self.prop = self.__comm.get_properties()
            self.prop['protoype'] = self.__code.get_properties()
        except:
            raise

    def generate_md(self):

        temp_prop = self.prop
        if temp_prop['params']:
            header = '''| NAME | TYPE | DESCRIPTION |
|------ | ------ | -------------|
'''
            param_str = str()
            for each_list in temp_prop['params']:
                param_str += ('|' + '|'.join(each_list) + '|\n')
            temp_prop['params'] = header + param_str

        if temp_prop['returns']:
            header = '''|TYPE | DESCRIPTION |
|------|-------------|
'''
            ret_str = str()
            for each_list in temp_prop['returns']:
                ret_str += ('|' + '|'.join(each_list) + '|\n')
            temp_prop['returns'] = header + ret_str

        md_string = '''
## **{name}**

> {desc}

```
{protoype}
```

### PARAMETERS:
{params}
### RETURN VALUE
{returns}


___
        '''.format(**self.prop)
        with open(self.__file_name, 'a') as md:
            md.write(md_string)

    def __str__(self):
        return self.__comm.__str__() + "\n" + self.__code.__str__()

    def __repr__(self):
        return self.__str__()


class parser():
    def __order_segments(self, segments_list):
        # segments_list is supposed to be a list of triplets of integers like this:
        # [(1, 0, 14), (3, 0, 4), (2, 0, 7), (16, 0, 17), (15, 0, 18),
        #                (10, 0,13), (5,0, 6), (8,0, 9), (11, 0,12)]
        # Each triplet denoting (comm_start, comm_end, segment_end)
        limit = max([max(e) for e in segments_list]) + 1
        segments_list.append((
            -1,
            -1,
            limit, ))
        segments_list.sort(key=lambda ele: ele[0])

        def core_order_segments(passed_idx):
            # TODO: Fix extra appends at the end of list
            current_tuple = segments_list[passed_idx]
            next_idx = passed_idx + 1
            while next_idx < len(segments_list):
                curr_pair_ans = []
                while current_tuple[0] < segments_list[next_idx][0] and segments_list[next_idx][2] < current_tuple[2]:
                    res = core_order_segments(next_idx)
                    if res is not None:
                        next_idx, temp_answer = res
                        curr_pair_ans.append(temp_answer)
                    else:
                        curr_pair_ans.append(
                            dict({
                                segments_list[next_idx]: []
                            }))
                        break
                return next_idx, dict({current_tuple: (curr_pair_ans)})
            return None

        return core_order_segments(0)

    def parse(self, file_name, dest_dir):

        # TODO: Remove any blank line from the file
        # TODO: Parse file char by char instead of line by line
        segments_found = []
        comm_start = None
        comm_end = None
        comm_and_open_paren = []

        with open(file_name) as f:
            src = f.readlines()
            for line_num, line in enumerate(src):
                line = line.strip()
                if line.startswith("/**"):
                    comm_start = line_num
                    comm_end = None

                if line.startswith("*/"):
                    comm_end = line_num

                if not (comm_start is not None and comm_end is None):
                    if ';' in line:
                        if comm_start is not None and comm_end is not None:
                            segments_found.append((comm_start, comm_end,
                                                   comm_end + 1))
                            comm_start = None
                            comm_end = None

                    if '{' in line:
                        comm_and_open_paren.append((
                            comm_start,
                            comm_end,
                            line_num, ))
                        comm_start = None
                        comm_end = None

                    if '}' in line:
                        possible_match = comm_and_open_paren.pop()
                        if possible_match[0] is not None and possible_match[1] is not None:
                            segments_found.append((
                                possible_match[0],
                                possible_match[1],
                                line_num, ))

            temp = []
            for each_segment in segments_found:
                comm = src[each_segment[0]:each_segment[1] + 1]
                code = src[each_segment[1] + 1:each_segment[2] + 1]
                obj = segment(comm, code, file_name, dest_dir)
                if obj is not None:
                    temp.append(obj)
            segments_found = temp
        return segments_found


if __name__ == "__main__":

    try:
        arg_parser = argparse.ArgumentParser(description="Cpp doc generator")
        arg_parser.add_argument(
            "-f", nargs='+', required=True, metavar="file_names", dest="files")
        arg_parser.add_argument(
            "-d",
            required=False,
            metavar="destination directory",
            dest="dest_dir",
            default=getcwd(),
            type=str)
        src_files = arg_parser.parse_args().files
        dest_dir = abspath(arg_parser.parse_args().dest_dir)

        if isdir(dest_dir):
            # Remove all existing md files for input files at destination directory
            for each_file in src_files:
                output_to_be = join(dest_dir,
                                    splitext(basename(each_file))[0] + ".md")
                print("Removing old..", output_to_be)
                if isfile(output_to_be):
                    remove(output_to_be)
            p = parser()
            for each_file in src_files:
                segments = p.parse(each_file, dest_dir)
                for each_segment in segments:
                    each_segment.generate_md()
            print("Markdowns Generated")
        else:
            raise Exception("Given destination is not a directory")
    except:
        raise
