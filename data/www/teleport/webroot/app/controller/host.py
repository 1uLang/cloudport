# -*- coding: utf-8 -*-

import time
import csv
import os
import json
import codecs
import ipaddress
import tornado.gen
import tornado.httpclient

from app.base.configs import tp_cfg
from app.const import *
from app.model import host
from app.model import account
from app.model import group
from app.base.core_server import core_service_async_enc
from app.base.logger import *
from app.base.controller import TPBaseHandler, TPBaseJsonHandler


class HostListHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_ASSET_CREATE | TP_PRIVILEGE_ASSET_DELETE | TP_PRIVILEGE_ASSET_GROUP)
        if ret != TPE_OK:
            return

        err, groups = group.get_host_groups_for_user(self.current_user['id'], self.current_user['privilege'])
        param = {
            'host_groups': groups
        }

        self.render('asset/host-list.mako', page_param=json.dumps(param))


class DoGetHostsHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_ASSET_CREATE | TP_PRIVILEGE_ASSET_DELETE | TP_PRIVILEGE_ASSET_GROUP)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        sql_filter = {}
        sql_order = dict()
        sql_order['name'] = 'id'
        sql_order['asc'] = True
        sql_limit = dict()
        sql_limit['page_index'] = 0
        sql_limit['per_page'] = 25
        sql_restrict = args['restrict'] if 'restrict' in args else {}
        sql_exclude = args['exclude'] if 'exclude' in args else {}

        try:
            tmp = list()
            _filter = args['filter']
            for i in _filter:
                # if i == 'role' and _filter[i] == 0:
                #     tmp.append(i)
                #     continue
                if i == 'state' and _filter[i] == 0:
                    tmp.append(i)
                    continue
                if i == 'search':
                    _x = _filter[i].strip()
                    if len(_x) == 0:
                        tmp.append(i)
                    continue
                elif i == 'host_group':
                    if _filter[i] == -1:
                        tmp.append(i)
                    continue

            for i in tmp:
                del _filter[i]

            sql_filter.update(_filter)

            _limit = args['limit']
            if _limit['page_index'] < 0:
                _limit['page_index'] = 0
            if _limit['per_page'] < 10:
                _limit['per_page'] = 10
            if _limit['per_page'] > 100:
                _limit['per_page'] = 100

            sql_limit.update(_limit)

            _order = args['order']
            if _order is not None:
                sql_order['name'] = _order['k']
                sql_order['asc'] = _order['v']

        except:
            return self.write_json(TPE_PARAM)

        err, total_count, page_index, row_data = \
            host.get_hosts(sql_filter, sql_order, sql_limit, sql_restrict, sql_exclude)
        ret = dict()
        ret['page_index'] = page_index
        ret['total'] = total_count
        ret['data'] = row_data
        self.write_json(err, data=ret)


class HostGroupListHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_ASSET_GROUP)
        if ret != TPE_OK:
            return
        self.render('asset/host-group-list.mako')


class HostGroupInfoHandler(TPBaseHandler):
    def get(self, gid):
        ret = self.check_privilege(TP_PRIVILEGE_ASSET_GROUP)
        if ret != TPE_OK:
            return
        gid = int(gid)
        err, groups = group.get_by_id(TP_GROUP_HOST, gid)
        if err == TPE_OK:
            param = {
                'group_id': gid,
                'group_name': groups['name'],
                'group_desc': groups['desc']
            }
        else:
            param = {
                'group_id': 0,
                'group_name': '',
                'group_desc': ''
            }

        self.render('asset/host-group-info.mako', page_param=json.dumps(param))


class DoImportHandler(TPBaseHandler):
    IDX_IP = 0
    IDX_OS = 1
    IDX_NAME = 2
    IDX_ROUTER_IP = 3
    IDX_ROUTER_PORT = 4
    IDX_IDC = 5
    IDX_USERNAME = 6
    IDX_PROTOCOL = 7
    IDX_PROTOCOL_PORT = 8
    IDX_AUTH = 9
    IDX_SECRET = 10
    IDX_USERNAME_PROMPT = 11
    IDX_PASSWORD_PROMPT = 12
    IDX_GROUP = 13
    IDX_DESC = 14

    @tornado.gen.coroutine
    def post(self):
        """
        csv???????????????
        ???????????????????????????
          ??????IP,??????????????????,??????,??????IP,????????????,????????????,??????,????????????,????????????,????????????,???????????????,????????????,????????????,??????,??????
        ???????????????
          0. ??????#?????????????????????
          1. ??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
          2. ???????????????????????????????????????????????????|????????????????????????????????????????????????????????????????????????
          3. ????????????????????????????????????????????????
        """
        ret = dict()
        ret['code'] = TPE_OK
        ret['message'] = ''

        rv = self.check_privilege(
            TP_PRIVILEGE_ASSET_CREATE | TP_PRIVILEGE_ASSET_GROUP | TP_PRIVILEGE_USER_CREATE | TP_PRIVILEGE_USER_GROUP,
            need_process=False)
        if rv != TPE_OK:
            ret['code'] = rv
            if rv == TPE_NEED_LOGIN:
                ret['message'] = '???????????????'
            elif rv == TPE_PRIVILEGE:
                ret['message'] = '???????????????'
            else:
                ret['message'] = '???????????????'
            return self.write(json.dumps(ret).encode('utf8'))

        # success = list()
        failed = list()
        group_failed = list()
        csv_filename = ''

        try:
            upload_path = os.path.join(tp_cfg().data_path, 'tmp')  # ?????????????????????
            if not os.path.exists(upload_path):
                os.mkdir(upload_path)
            file_metas = self.request.files['csvfile']  # ??????????????????name?????????file?????????????????????
            for meta in file_metas:
                now = time.localtime(time.time())
                tmp_name = 'upload-{:04d}{:02d}{:02d}{:02d}{:02d}{:02d}.csv'.format(
                    now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
                csv_filename = os.path.join(upload_path, tmp_name)
                with open(csv_filename, 'wb') as f:
                    f.write(meta['body'])

            # file encode maybe utf8 or gbk... check it out.
            file_encode = None
            with codecs.open(csv_filename, 'r', encoding='gbk') as f:
                try:
                    f.readlines()
                    file_encode = 'gbk'
                except:
                    pass

            if file_encode is None:
                log.v('file `{}` is not gbk, try utf8\n'.format(csv_filename))
                with codecs.open(csv_filename, 'r', encoding='utf_8_sig') as f:
                    try:
                        f.readlines()
                        file_encode = 'utf_8_sig'
                    except:
                        pass

            if file_encode is None:
                os.remove(csv_filename)
                log.e('file `{}` unknown encode, neither GBK nor UTF8.\n'.format(csv_filename))
                ret['code'] = TPE_FAILED
                ret['message'] = '???????????????????????????GBK????????????UTF8?????????'
                return self.write(json.dumps(ret).encode('utf8'))

            host_groups = dict()  # ?????????????????????????????????
            acc_groups = dict()  # ?????????????????????????????????
            hosts = dict()  # ????????????????????????????????????????????????????????????????????????????????????????????????

            # ??????csv??????
            with open(csv_filename, encoding=file_encode) as f:
                all_acc = []  # ?????????????????????????????????????????????
                csv_reader = csv.reader(f)
                line = 0
                last_ip = None
                for csv_recorder in csv_reader:
                    line += 1

                    # ?????????????????????
                    if len(csv_recorder) == 0 or csv_recorder[0].strip().startswith('#'):
                        continue

                    # ??????????????????????????????????????????
                    if len(csv_recorder) != 15:
                        failed.append({'line': line, 'error': '???????????????????????????????????????'})
                        continue

                    # check
                    _ip = csv_recorder[self.IDX_IP].strip()
                    _username = csv_recorder[self.IDX_USERNAME].strip()
                    if len(_ip) == 0 and len(_username) == 0:
                        failed.append({'line': line, 'error': '?????????????????????IP???????????????'})
                        continue

                    # ????????????
                    _group = list()
                    for g in csv_recorder[self.IDX_GROUP].split('|'):
                        g = g.strip()
                        if len(g) > 0 and g not in _group:
                            _group.append(g)
                    _desc = csv_recorder[self.IDX_DESC].strip().replace("\\n", "\n")

                    if len(_ip) > 0:
                        last_ip = None

                        try:
                            ipaddress.ip_address(_ip)
                        except:
                            failed.append({'line': line, 'error': '??????????????????????????????IP?????????'})
                            continue

                        if _ip in hosts:
                            failed.append({'line': line, 'error': '???????????????'})
                            continue

                        # ??????????????????
                        _host_os = csv_recorder[self.IDX_OS].strip().upper()
                        if _host_os == 'WIN' or _host_os == 'WINDOWS':
                            _host_os = TP_OS_TYPE_WINDOWS
                        elif _host_os == 'LINUX':
                            _host_os = TP_OS_TYPE_LINUX
                        else:
                            failed.append({'line': line, 'error': '???????????????????????????????????????????????????'})
                            continue

                        _router_ip = csv_recorder[self.IDX_ROUTER_IP].strip()
                        _router_port = csv_recorder[self.IDX_ROUTER_PORT].strip()

                        if not (
                                (len(_router_ip) == 0 and len(_router_port) == 0)
                                or (len(_router_ip) > 0 and len(_router_port) > 0)
                        ):
                            failed.append({'line': line, 'error': '??????????????????????????????IP?????????????????????'})
                            continue
                        if len(_router_ip) > 0:
                            try:
                                ipaddress.ip_address(_ip)
                            except:
                                failed.append({'line': line, 'error': '??????????????????????????????IP?????????'})
                                continue
                            try:
                                _router_port = int(_router_port)
                            except:
                                failed.append({'line': line, 'error': '???????????????????????????????????????'})
                                continue
                            if _router_port < 0 or _router_port > 65535:
                                failed.append({'line': line, 'error': '???????????????????????????????????????'})
                                continue
                        else:
                            _router_port = 0

                        _host = dict()
                        _host['_line'] = line
                        _host['ip'] = _ip
                        _host['os'] = _host_os
                        _host['name'] = csv_recorder[self.IDX_NAME].strip()
                        _host['router_ip'] = _router_ip
                        _host['router_port'] = _router_port
                        _host['cid'] = csv_recorder[self.IDX_IDC].strip()
                        _host['group'] = _group
                        _host['desc'] = _desc
                        _host['acc'] = list()

                        hosts[_ip] = _host

                        last_ip = _ip

                    else:
                        # account
                        if last_ip is None:
                            failed.append({'line': line, 'error': '?????????????????????????????????'})
                            continue

                        _protocol = csv_recorder[self.IDX_PROTOCOL].strip().upper()
                        if _protocol == 'RDP':
                            _protocol = TP_PROTOCOL_TYPE_RDP
                        elif _protocol == 'SSH':
                            _protocol = TP_PROTOCOL_TYPE_SSH
                        elif _protocol == 'TELNET':
                            _protocol = TP_PROTOCOL_TYPE_TELNET
                        else:
                            failed.append({'line': line, 'error': '?????????????????????????????????????????????'})
                            continue

                        _protocol_port = csv_recorder[self.IDX_PROTOCOL_PORT].strip()
                        if hosts[last_ip]['router_port'] == 0:
                            if len(_protocol_port) == 0:
                                failed.append({'line': line, 'error': '????????????????????????????????????????????????'})
                                continue
                            try:
                                _protocol_port = int(_protocol_port)
                            except:
                                failed.append({'line': line, 'error': '???????????????????????????????????????????????????'})
                                continue
                        else:
                            _protocol_port = 0

                        _auth = csv_recorder[self.IDX_AUTH].strip().upper()
                        if _auth == 'NO':
                            _auth = TP_AUTH_TYPE_NONE
                        elif _auth == 'PW':
                            _auth = TP_AUTH_TYPE_PASSWORD
                        elif _auth == 'KEY':
                            _auth = TP_AUTH_TYPE_PRIVATE_KEY
                        else:
                            failed.append({'line': line, 'error': '???????????????????????????????????????'})
                            continue

                        _secret = csv_recorder[self.IDX_SECRET].strip()
                        if _auth != TP_AUTH_TYPE_NONE and len(_secret) == 0:
                            failed.append({'line': line, 'error': '?????????????????????????????????????????????'})
                            continue

                        _username_prompt = csv_recorder[self.IDX_USERNAME_PROMPT].strip()
                        _password_prompt = csv_recorder[self.IDX_PASSWORD_PROMPT].strip()
                        if _protocol != TP_PROTOCOL_TYPE_TELNET:
                            _username_prompt = ''
                            _password_prompt = ''

                        _acc_info = '{}-{}-{}'.format(last_ip, _username, _auth)
                        if _acc_info in all_acc:
                            failed.append({'line': line, 'error': '???????????????'})
                            continue
                        all_acc.append(_acc_info)

                        _acc = dict()
                        _acc['_line'] = line
                        _acc['username'] = _username
                        _acc['protocol_type'] = _protocol
                        _acc['protocol_port'] = _protocol_port
                        _acc['auth_type'] = _auth
                        _acc['secret'] = _secret
                        _acc['username_prompt'] = _username_prompt
                        _acc['password_prompt'] = _password_prompt
                        _acc['group'] = _group
                        _acc['desc'] = _desc

                        hosts[last_ip]['acc'].append(_acc)

            if os.path.exists(csv_filename):
                os.remove(csv_filename)

            # ???????????????????????????????????????????????????
            if len(failed) > 0:
                ret['code'] = TPE_FAILED
                ret['message'] = '??????????????????????????????????????????????????????'
                ret['data'] = failed
                return self.write(json.dumps(ret).encode('utf8'))

            if len(hosts) == 0:
                ret['code'] = TPE_FAILED
                ret['message'] = '????????? csv ??????????????????????????????????????????'
                ret['data'] = failed
                return self.write(json.dumps(ret).encode('utf8'))

            # ???????????????????????????????????????????????????????????????
            for ip in hosts:
                for i in range(len(hosts[ip]['acc'])):
                    if len(hosts[ip]['acc'][i]['secret']) == 0:
                        continue
                    code, ret_data = yield core_service_async_enc(hosts[ip]['acc'][i]['secret'])
                    if code != TPE_OK:
                        ret['code'] = code
                        ret['message'] = '?????????????????????????????????'
                        if code == TPE_NO_CORE_SERVER:
                            ret['message'] += '?????????????????????????????????'
                        ret['data'] = failed
                        return self.write(json.dumps(ret).encode('utf8'))
                    hosts[ip]['acc'][i]['secret'] = ret_data

            # ?????????????????????????????????????????????
            for ip in hosts:
                for g in hosts[ip]['group']:
                    if g not in host_groups:
                        host_groups[g] = 0
                for i in range(len(hosts[ip]['acc'])):
                    for g in hosts[ip]['acc'][i]['group']:
                        if g not in acc_groups:
                            acc_groups[g] = 0

            # ?????????????????????????????????????????????????????????????????????????????????????????????id??????????????????
            if len(host_groups) > 0:
                err = group.make_groups(self, TP_GROUP_HOST, host_groups, group_failed)
                if len(group_failed) > 0:
                    ret['code'] = TPE_FAILED
                    ret['message'] += '????????????????????? {}???'.format('???'.join(group_failed))
                    return self.write(json.dumps(ret).encode('utf8'))

            if len(acc_groups) > 0:
                err = group.make_groups(self, TP_GROUP_ACCOUNT, acc_groups, group_failed)
                if len(group_failed) > 0:
                    ret['code'] = TPE_FAILED
                    ret['message'] += '????????????????????? {}???'.format('???'.join(group_failed))
                    return self.write(json.dumps(ret).encode('utf8'))

            # ?????????????????????
            for ip in hosts:
                # router_addr = ''
                # if hosts[ip]['router_port'] > 0:
                #     router_addr = '{}:{}'.format(hosts[ip]['router_ip'], hosts[ip]['router_port'])

                args = dict()
                args['ip'] = ip
                args['router_ip'] = hosts[ip]['router_ip']
                args['router_port'] = hosts[ip]['router_port']
                args['os_type'] = hosts[ip]['os']
                args['name'] = hosts[ip]['name']
                args['cid'] = hosts[ip]['cid']
                args['desc'] = hosts[ip]['desc']
                err, host_id = host.add_host(self, args)
                if err != TPE_OK:
                    hosts[ip]['host_id'] = 0
                    if err == TPE_EXISTS:
                        failed.append({'line': hosts[ip]['_line'], 'error': '????????????{}?????????????????????????????????'.format(ip)})
                    else:
                        failed.append({'line': hosts[ip]['_line'], 'error': '????????????{}?????????????????????????????????'.format(ip)})
                    continue
                hosts[ip]['host_id'] = host_id

                for i in range(len(hosts[ip]['acc'])):
                    args = dict()
                    args['host_ip'] = ip
                    args['router_ip'] = hosts[ip]['router_ip']
                    args['router_port'] = hosts[ip]['router_port']
                    # args['host_router_addr'] = router_addr
                    args['host_id'] = host_id
                    args['protocol_type'] = hosts[ip]['acc'][i]['protocol_type']
                    args['protocol_port'] = hosts[ip]['acc'][i]['protocol_port']
                    args['auth_type'] = hosts[ip]['acc'][i]['auth_type']
                    args['username'] = hosts[ip]['acc'][i]['username']
                    args['password'] = ''
                    args['pri_key'] = ''
                    if args['auth_type'] == TP_AUTH_TYPE_PASSWORD:
                        args['password'] = hosts[ip]['acc'][i]['secret']
                    elif args['auth_type'] == TP_AUTH_TYPE_PRIVATE_KEY:
                        args['pri_key'] = hosts[ip]['acc'][i]['secret']

                    args['username_prompt'] = _acc['username_prompt']
                    args['password_prompt'] = _acc['password_prompt']

                    err, acc_id = account.add_account(self, host_id, args)
                    if err == TPE_EXISTS:
                        failed.append({
                            'line': hosts[ip]['acc']['_line'],
                            'error': '????????????{}@{}??????????????????????????????'.format(args['username'], ip)
                        })
                        continue
                    elif err != TPE_OK:
                        failed.append({
                            'line': hosts[ip]['acc']['_line'],
                            'error': '????????????{}@{}?????????????????????????????????'.format(args['username'], ip)
                        })

                    hosts[ip]['acc'][i]['acc_id'] = acc_id

            # ???????????????????????????????????????????????????
            for ip in hosts:
                if hosts[ip]['host_id'] == 0:
                    continue

                gm = list()
                for hg in hosts[ip]['group']:
                    for g in host_groups:
                        if host_groups[g] == 0 or hg != g:
                            continue
                        gm.append({'type': 2, 'gid': host_groups[g], 'mid': hosts[ip]['host_id']})

                group.make_group_map(TP_GROUP_HOST, gm)

                for i in range(len(hosts[ip]['acc'])):
                    if hosts[ip]['acc'][i]['acc_id'] == 0:
                        continue

                    gm = list()
                    for ag in hosts[ip]['acc'][i]['group']:
                        for g in acc_groups:
                            if acc_groups[g] == 0 or ag != g:
                                continue
                            gm.append({'type': 3, 'gid': acc_groups[g], 'mid': hosts[ip]['acc'][i]['acc_id']})

                    group.make_group_map(TP_GROUP_ACCOUNT, gm)

            # ret['code'] = TPE_FAILED
            # ret['message'] = '-----------???'
            # ret['data'] = failed
            # return self.write(json.dumps(ret).encode('utf8'))

            #
            # # ????????????????????????????????????????????????????????????????????????
            # gm = list()
            # for u in user_list:
            #     if u['_id'] == 0:
            #         continue
            #     for ug in u['_group']:
            #         for g in group_list:
            #             if group_list[g] == 0 or ug != g:
            #                 continue
            #             gm.append({'type': 1, 'gid': group_list[g], 'mid': u['_id']})
            #
            # user.make_user_group_map(gm)
            #
            if len(failed) == 0:
                ret['code'] = TPE_OK
                # ret['message'] = '?????? {} ??????????????????????????????'.format(len(success))
                ret['message'] = '??????????????????????????????'
                return self.write(json.dumps(ret).encode('utf8'))
            else:
                ret['code'] = TPE_FAILED
                # if len(success) > 0:
                #     ret['message'] = '{} ??????????????????????????????'.format(len(success))
                ret['message'] = '????????????????????????????????????'
                ret['message'] += '{} ?????????????????????????????????'.format(len(failed))

                ret['data'] = failed
                return self.write(json.dumps(ret).encode('utf8'))
        except:
            log.e('got exception when import host and account.\n')
            ret['code'] = TPE_FAILED
            # if len(success) > 0:
            #     ret['message'] += '{} ???????????????????????????????????????'.format(len(success))
            # else:
            #     ret['message'] = '???????????????'
            ret['message'] = '???????????????'
            if len(failed) > 0:
                ret['data'] = failed
            return self.write(json.dumps(ret).encode('utf8'))


class DoUpdateHostHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_ASSET_CREATE | TP_PRIVILEGE_ASSET_DELETE | TP_PRIVILEGE_ASSET_GROUP)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            args['id'] = int(args['id'])
            args['os_type'] = int(args['os_type'])
            args['ip'] = args['ip'].strip()
            args['router_ip'] = args['router_ip']
            args['router_port'] = int(args['router_port'])
            args['name'] = args['name'].strip()
            args['cid'] = args['cid'].strip()
            args['desc'] = args['desc'].strip()
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        if len(args['ip']) == 0:
            return self.write_json(TPE_PARAM)

        if args['id'] == -1:
            err, info = host.add_host(self, args)
        else:
            err = host.update_host(self, args)
            info = {}
        self.write_json(err, data=info)


class DoUpdateHostsHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_ASSET_DELETE)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            action = args['action']
            host_ids = args['hosts']
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        if len(host_ids) == 0:
            return self.write_json(TPE_PARAM)

        if action == 'lock':
            err = host.update_hosts_state(self, host_ids, TP_STATE_DISABLED)
            return self.write_json(err)
        elif action == 'unlock':
            err = host.update_hosts_state(self, host_ids, TP_STATE_NORMAL)
            return self.write_json(err)
        elif action == 'remove':
            err = host.remove_hosts(self, host_ids)
            return self.write_json(err)
        else:
            return self.write_json(TPE_PARAM)


class DoGetHostGroupWithMemberHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_ASSET_GROUP)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        sql_filter = {}
        sql_order = dict()
        sql_order['name'] = 'id'
        sql_order['asc'] = True
        sql_limit = dict()
        sql_limit['page_index'] = 0
        sql_limit['per_page'] = 25

        try:
            tmp = list()
            _filter = args['filter']
            for i in _filter:
                if i == 'search':
                    _x = _filter[i].strip()
                    if len(_x) == 0:
                        tmp.append(i)
                    continue

            for i in tmp:
                del _filter[i]

            sql_filter.update(_filter)

            _limit = args['limit']
            if _limit['page_index'] < 0:
                _limit['page_index'] = 0
            if _limit['per_page'] < 10:
                _limit['per_page'] = 10
            if _limit['per_page'] > 100:
                _limit['per_page'] = 100

            sql_limit.update(_limit)

            _order = args['order']
            if _order is not None:
                sql_order['name'] = _order['k']
                sql_order['asc'] = _order['v']

        except:
            return self.write_json(TPE_PARAM)

        err, total_count, row_data = host.get_group_with_member(sql_filter, sql_order, sql_limit)
        ret = dict()
        ret['page_index'] = sql_limit['page_index']
        ret['total'] = total_count
        ret['data'] = row_data
        self.write_json(err, data=ret)
