#coding:utf-8
#
#   PROGRAM/MODULE: fdb
#   FILE:           ibase.py
#   DESCRIPTION:    Python ctypes interface to Firebird client library
#   CREATED:        6.10.2011
#
#  Software distributed under the License is distributed AS IS,
#  WITHOUT WARRANTY OF ANY KIND, either express or implied.
#  See the License for the specific language governing rights
#  and limitations under the License.
#
#  The Original Code was created by Pavel Cisar
#
#  Copyright (c) 2011 Pavel Cisar <pcisar@users.sourceforge.net>
#  and all contributors signed below.
#
#  All Rights Reserved.
#  Contributor(s): Philippe Makowski <pmakowski@ibphoenix.fr>
#                  ______________________________________.
#
# See LICENSE.TXT for details.
import os
import sys
import types
import locale
import operator
libpath = os.path.join(os.path.dirname(__file__), 'lib') + os.pathsep
if libpath not in os.environ['PATH']:
    os.environ['PATH'] = libpath + os.environ['PATH']

PYTHON_MAJOR_VER = sys.version_info[0]

#-------------------

if PYTHON_MAJOR_VER == 3:
    from queue import PriorityQueue
    def nativestr(st,charset="latin-1"):
        if st == None:
            return st
        elif isinstance(st, bytes):
            return st.decode(charset)
        else:
            return st
    def b(st,charset="latin-1"):
        if st == None:
            return st
        elif isinstance(st, bytes):
            return st
        else:
            try:
                return st.encode(charset)
            except UnicodeEncodeError:
                return st

    def s(st):
        return st

    ord2 = lambda x: x if type(x) == IntType else ord(x)

    if sys.version_info[1] <= 1:
        def int2byte(i):
            return bytes((i,))
    else:
        # This is about 2x faster than the implementation above on 3.2+
        int2byte = operator.methodcaller("to_bytes", 1, "big")

    def mychr(i):
        return i

    mybytes = bytes
    myunicode = str
    mylong = int
    StringType = str
    IntType = int
    LongType = int
    FloatType = float
    ListType = list
    UnicodeType = str
    TupleType = tuple
    xrange = range

else:
    from Queue import PriorityQueue
    def nativestr(st,charset="latin-1"):
        if st == None:
            return st
        elif isinstance(st, unicode):
            return st.encode(charset)
        else:
            return st
    def b(st,charset="latin-1"):
        if st == None:
            return st
        elif isinstance(st, types.StringType):
            return st
        else:
            try:
                return st.encode(charset)
            except UnicodeEncodeError:
                return st

    int2byte = chr
    s = str
    ord2 = ord

    def mychr(i):
        return chr(i)

    mybytes = str
    myunicode = unicode
    mylong = long
    StringType = types.StringType
    IntType = types.IntType
    LongType = types.LongType
    FloatType = types.FloatType
    ListType = types.ListType
    UnicodeType = types.UnicodeType
    TupleType = types.TupleType
    xrange = xrange

# ibase.h

FB_API_VER = 25
MAX_BLOB_SEGMENT_SIZE = 65535

# Event queue operation (and priority) codes

OP_DIE      = 1
OP_RECORD_AND_REREGISTER = 2

charset_map = {
    # DB CHAR SET NAME    :   PYTHON CODEC NAME (CANONICAL)
    # -------------------------------------------------------------------------
    None                  :   locale.getpreferredencoding(),
    'NONE'                :   locale.getpreferredencoding(),
    'OCTETS'              :   None,  # Allow to pass through unchanged.
    'UNICODE_FSS'         :   'utf_8',
    'UTF8'                :   'utf_8',  # (Firebird 2.0+)
    'SJIS_0208'           :   'shift_jis',
    'EUCJ_0208'           :   'euc_jp',
    'DOS737'              :   'cp737',
    'DOS437'              :   'cp437',
    'DOS850'              :   'cp850',
    'DOS865'              :   'cp865',
    'DOS860'              :   'cp860',
    'DOS863'              :   'cp863',
    'DOS775'              :   'cp775',
    'DOS862'              :   'cp862',
    'DOS864'              :   'cp864',
    'ISO8859_1'           :   'iso8859_1',
    'ISO8859_2'           :   'iso8859_2',
    'ISO8859_3'           :   'iso8859_3',
    'ISO8859_4'           :   'iso8859_4',
    'ISO8859_5'           :   'iso8859_5',
    'ISO8859_6'           :   'iso8859_6',
    'ISO8859_7'           :   'iso8859_7',
    'ISO8859_8'           :   'iso8859_8',
    'ISO8859_9'           :   'iso8859_9',
    'ISO8859_13'          :   'iso8859_13',
    'KSC_5601'            :   'euc_kr',
    'DOS852'              :   'cp852',
    'DOS857'              :   'cp857',
    'DOS861'              :   'cp861',
    'DOS866'              :   'cp866',
    'DOS869'              :   'cp869',
    'WIN1250'             :   'cp1250',
    'WIN1251'             :   'cp1251',
    'WIN1252'             :   'cp1252',
    'WIN1253'             :   'cp1253',
    'WIN1254'             :   'cp1254',
    'BIG_5'               :   'big5',
    'GB_2312'             :   'gb2312',
    'WIN1255'             :   'cp1255',
    'WIN1256'             :   'cp1256',
    'WIN1257'             :   'cp1257',
    'KOI8-R'              :   'koi8_r',  # (Firebird 2.0+)
    'KOI8-U'              :   'koi8_u',  # (Firebird 2.0+)
    'WIN1258'             :   'cp1258',  # (Firebird 2.0+)
    }

DB_CHAR_SET_NAME_TO_PYTHON_ENCODING_MAP = charset_map

# C integer limit constants

SHRT_MIN = -32767
SHRT_MAX = 32767
USHRT_MAX = 65535
INT_MIN = -2147483648
INT_MAX = 2147483647
LONG_MIN = -9223372036854775808
LONG_MAX = 9223372036854775807
SSIZE_T_MIN = INT_MIN
SSIZE_T_MAX = INT_MAX

# Constants

DSQL_close = 1
DSQL_drop = 2
DSQL_unprepare = 4
SQLDA_version1 = 1

# Type codes

SQL_TEXT = 452
SQL_VARYING = 448
SQL_SHORT = 500
SQL_LONG = 496
SQL_FLOAT = 482
SQL_DOUBLE = 480
SQL_D_FLOAT = 530
SQL_TIMESTAMP = 510
SQL_BLOB = 520
SQL_ARRAY = 540
SQL_QUAD = 550
SQL_TYPE_TIME = 560
SQL_TYPE_DATE = 570
SQL_INT64 = 580

SUBTYPE_NUMERIC = 1
SUBTYPE_DECIMAL = 2

# Internal type codes (for example used by ARRAY descriptor)

blr_text = 14
blr_text2 = 15
blr_short = 7
blr_long = 8
blr_quad = 9
blr_float = 10
blr_double = 27
blr_d_float = 11
blr_timestamp = 35
blr_varying = 37
blr_varying2 = 38
blr_blob = 261
blr_cstring = 40
blr_cstring2 = 41
blr_blob_id = 45
blr_sql_date = 12
blr_sql_time = 13
blr_int64 = 16
blr_blob2 = 17
# Added in FB 2.1
blr_domain_name = 18
blr_domain_name2 = 19
blr_not_nullable = 20
# Added in FB 2.5
blr_column_name = 21
blr_column_name2 = 22
blr_domain_type_of = 0
blr_domain_full = 1
# Rest of BLR is defined in fdb.blr

# Database parameter block stuff

isc_dpb_version1 = 1
isc_dpb_cdd_pathname = 1
isc_dpb_allocation = 2
isc_dpb_journal = 3
isc_dpb_page_size = 4
isc_dpb_num_buffers = 5
isc_dpb_buffer_length = 6
isc_dpb_debug = 7
isc_dpb_garbage_collect = 8
isc_dpb_verify = 9
isc_dpb_sweep = 10
isc_dpb_enable_journal = 11
isc_dpb_disable_journal = 12
isc_dpb_dbkey_scope = 13
isc_dpb_number_of_users = 14
isc_dpb_trace = 15
isc_dpb_no_garbage_collect = 16
isc_dpb_damaged = 17
isc_dpb_license = 18
isc_dpb_sys_user_name = 19
isc_dpb_encrypt_key = 20
isc_dpb_activate_shadow = 21
isc_dpb_sweep_interval = 22
isc_dpb_delete_shadow = 23
isc_dpb_force_write = 24
isc_dpb_begin_log = 25
isc_dpb_quit_log = 26
isc_dpb_no_reserve = 27
isc_dpb_user_name = 28
isc_dpb_password = 29
isc_dpb_password_enc = 30
isc_dpb_sys_user_name_enc = 31
isc_dpb_interp = 32
isc_dpb_online_dump = 33
isc_dpb_old_file_size = 34
isc_dpb_old_num_files = 35
isc_dpb_old_file = 36
isc_dpb_old_start_page = 37
isc_dpb_old_start_seqno = 38
isc_dpb_old_start_file = 39
isc_dpb_drop_walfile = 40
isc_dpb_old_dump_id = 41
isc_dpb_wal_backup_dir = 42
isc_dpb_wal_chkptlen = 43
isc_dpb_wal_numbufs = 44
isc_dpb_wal_bufsize = 45
isc_dpb_wal_grp_cmt_wait = 46
isc_dpb_lc_messages = 47
isc_dpb_lc_ctype = 48
isc_dpb_cache_manager = 49
isc_dpb_shutdown = 50
isc_dpb_online = 51
isc_dpb_shutdown_delay = 52
isc_dpb_reserved = 53
isc_dpb_overwrite = 54
isc_dpb_sec_attach = 55
isc_dpb_disable_wal = 56
isc_dpb_connect_timeout = 57
isc_dpb_dummy_packet_interval = 58
isc_dpb_gbak_attach = 59
isc_dpb_sql_role_name = 60
isc_dpb_set_page_buffers = 61
isc_dpb_working_directory = 62
isc_dpb_sql_dialect = 63
isc_dpb_set_db_readonly = 64
isc_dpb_set_db_sql_dialect = 65
isc_dpb_gfix_attach = 66
isc_dpb_gstat_attach = 67
isc_dpb_set_db_charset = 68
isc_dpb_gsec_attach = 69
isc_dpb_address_path = 70
# Added in FB 2.1
isc_dpb_process_id = 71
isc_dpb_no_db_triggers = 72
isc_dpb_trusted_auth = 73
isc_dpb_process_name = 74
# Added in FB 2.5
isc_dpb_trusted_role = 75
isc_dpb_org_filename = 76
isc_dpb_utf8_filename = 77
isc_dpb_ext_call_depth = 78

# structural codes
isc_info_end = 1
isc_info_truncated = 2
isc_info_error = 3
isc_info_data_not_ready = 4
isc_info_length = 126
isc_info_flag_end = 127

isc_info_req_select_count = 13
isc_info_req_insert_count = 14
isc_info_req_update_count = 15
isc_info_req_delete_count = 16

# DB Info item codes
isc_info_db_id = 4
isc_info_reads = 5
isc_info_writes = 6
isc_info_fetches = 7
isc_info_marks = 8
isc_info_implementation = 11
isc_info_isc_version = 12
isc_info_base_level = 13
isc_info_page_size = 14
isc_info_num_buffers = 15
isc_info_limbo = 16
isc_info_current_memory = 17
isc_info_max_memory = 18
isc_info_window_turns = 19
isc_info_license = 20
isc_info_allocation = 21
isc_info_attachment_id = 22
isc_info_read_seq_count = 23
isc_info_read_idx_count = 24
isc_info_insert_count = 25
isc_info_update_count = 26
isc_info_delete_count = 27
isc_info_backout_count = 28
isc_info_purge_count = 29
isc_info_expunge_count = 30
isc_info_sweep_interval = 31
isc_info_ods_version = 32
isc_info_ods_minor_version = 33
isc_info_no_reserve = 34
isc_info_logfile = 35
isc_info_cur_logfile_name = 36
isc_info_cur_log_part_offset = 37
isc_info_num_wal_buffers = 38
isc_info_wal_buffer_size = 39
isc_info_wal_ckpt_length = 40
isc_info_wal_cur_ckpt_interval = 41
isc_info_wal_prv_ckpt_fname = 42
isc_info_wal_prv_ckpt_poffset = 43
isc_info_wal_recv_ckpt_fname = 44
isc_info_wal_recv_ckpt_poffset = 45
isc_info_wal_grpc_wait_usecs = 47
isc_info_wal_num_io = 48
isc_info_wal_avg_io_size = 49
isc_info_wal_num_commits = 50
isc_info_wal_avg_grpc_size = 51
isc_info_forced_writes = 52
isc_info_user_names = 53
isc_info_page_errors = 54
isc_info_record_errors = 55
isc_info_bpage_errors = 56
isc_info_dpage_errors = 57
isc_info_ipage_errors = 58
isc_info_ppage_errors = 59
isc_info_tpage_errors = 60
isc_info_set_page_buffers = 61
isc_info_db_sql_dialect = 62
isc_info_db_read_only = 63
isc_info_db_size_in_pages = 64
# Values 65 -100 unused to avoid conflict with InterBase
frb_info_att_charset = 101
isc_info_db_class = 102
isc_info_firebird_version = 103
isc_info_oldest_transaction = 104
isc_info_oldest_active = 105
isc_info_oldest_snapshot = 106
isc_info_next_transaction = 107
isc_info_db_provider = 108
isc_info_active_transactions = 109
isc_info_active_tran_count = 110
isc_info_creation_date = 111
isc_info_db_file_size = 112 # added in FB 2.1
fb_info_page_contents = 113 # added in FB 2.5
isc_info_db_last_value = (fb_info_page_contents + 1)

isc_info_version = isc_info_isc_version

# Blob information items
isc_info_blob_num_segments = 4
isc_info_blob_max_segment = 5
isc_info_blob_total_length = 6
isc_info_blob_type = 7

# Transaction information items

isc_info_tra_id = 4
isc_info_tra_oldest_interesting = 5
isc_info_tra_oldest_snapshot = 6
isc_info_tra_oldest_active = 7
isc_info_tra_isolation = 8
isc_info_tra_access = 9
isc_info_tra_lock_timeout = 10

# isc_info_tra_isolation responses
isc_info_tra_consistency = 1
isc_info_tra_concurrency = 2
isc_info_tra_read_committed = 3

# isc_info_tra_read_committed options
isc_info_tra_no_rec_version = 0
isc_info_tra_rec_version = 1

# isc_info_tra_access responses
isc_info_tra_readonly = 0
isc_info_tra_readwrite = 1

# SQL information items
isc_info_sql_select = 4
isc_info_sql_bind = 5
isc_info_sql_num_variables = 6
isc_info_sql_describe_vars = 7
isc_info_sql_describe_end = 8
isc_info_sql_sqlda_seq = 9
isc_info_sql_message_seq = 10
isc_info_sql_type = 11
isc_info_sql_sub_type = 12
isc_info_sql_scale = 13
isc_info_sql_length = 14
isc_info_sql_null_ind = 15
isc_info_sql_field = 16
isc_info_sql_relation = 17
isc_info_sql_owner = 18
isc_info_sql_alias = 19
isc_info_sql_sqlda_start = 20
isc_info_sql_stmt_type = 21
isc_info_sql_get_plan = 22
isc_info_sql_records = 23
isc_info_sql_batch_fetch = 24
isc_info_sql_relation_alias = 25

# SQL information return values
isc_info_sql_stmt_select = 1
isc_info_sql_stmt_insert = 2
isc_info_sql_stmt_update = 3
isc_info_sql_stmt_delete = 4
isc_info_sql_stmt_ddl = 5
isc_info_sql_stmt_get_segment = 6
isc_info_sql_stmt_put_segment = 7
isc_info_sql_stmt_exec_procedure = 8
isc_info_sql_stmt_start_trans = 9
isc_info_sql_stmt_commit = 10
isc_info_sql_stmt_rollback = 11
isc_info_sql_stmt_select_for_upd = 12
isc_info_sql_stmt_set_generator = 13
isc_info_sql_stmt_savepoint = 14

# Transaction parameter block stuff
isc_tpb_version1 = 1
isc_tpb_version3 = 3
isc_tpb_consistency = 1
isc_tpb_concurrency = 2
isc_tpb_shared = 3
isc_tpb_protected = 4
isc_tpb_exclusive = 5
isc_tpb_wait = 6
isc_tpb_nowait = 7
isc_tpb_read = 8
isc_tpb_write = 9
isc_tpb_lock_read = 10
isc_tpb_lock_write = 11
isc_tpb_verb_time = 12
isc_tpb_commit_time = 13
isc_tpb_ignore_limbo = 14
isc_tpb_read_committed = 15
isc_tpb_autocommit = 16
isc_tpb_rec_version = 17
isc_tpb_no_rec_version = 18
isc_tpb_restart_requests = 19
isc_tpb_no_auto_undo = 20
isc_tpb_lock_timeout = 21

# BLOB parameter buffer

isc_bpb_version1          = 1
isc_bpb_source_type       = 1
isc_bpb_target_type       = 2
isc_bpb_type              = 3
isc_bpb_source_interp     = 4
isc_bpb_target_interp     = 5
isc_bpb_filter_parameter  = 6
# Added in FB 2.1
isc_bpb_storage           = 7

isc_bpb_type_segmented    = 0
isc_bpb_type_stream       = 1
# Added in FB 2.1
isc_bpb_storage_main      = 0
isc_bpb_storage_temp      = 2

# BLOB codes

isc_segment    = 335544366
isc_segstr_eof = 335544367

# Services API
# Service parameter block stuff
isc_spb_current_version = 2
isc_spb_version = isc_spb_current_version
isc_spb_user_name = isc_dpb_user_name
isc_spb_sys_user_name = isc_dpb_sys_user_name
isc_spb_sys_user_name_enc = isc_dpb_sys_user_name_enc
isc_spb_password = isc_dpb_password
isc_spb_password_enc = isc_dpb_password_enc
isc_spb_command_line = 105
isc_spb_dbname = 106
isc_spb_verbose = 107
isc_spb_options = 108
isc_spb_address_path = 109
# Added in FB 2.1
isc_spb_process_id = 110
isc_spb_trusted_auth = 111
isc_spb_process_name = 112
# Added in FB 2.5
isc_spb_trusted_role = 113

# Service action items
isc_action_svc_backup = 1           # Starts database backup process on the server
isc_action_svc_restore = 2          # Starts database restore process on the server
isc_action_svc_repair = 3           # Starts database repair process on the server
isc_action_svc_add_user = 4         # Adds a new user to the security database
isc_action_svc_delete_user = 5      # Deletes a user record from the security database
isc_action_svc_modify_user = 6      # Modifies a user record in the security database
isc_action_svc_display_user = 7     # Displays a user record from the security database
isc_action_svc_properties = 8       # Sets database properties
isc_action_svc_add_license = 9      # Adds a license to the license file
isc_action_svc_remove_license = 10  # Removes a license from the license file
isc_action_svc_db_stats = 11        # Retrieves database statistics
isc_action_svc_get_ib_log = 12      # Retrieves the InterBase log file from the server
isc_action_svc_get_fb_log = 12      # Retrieves the Firebird log file from the server
# Added in FB 2.5
isc_action_svc_nbak = 20
isc_action_svc_nrest = 21
isc_action_svc_trace_start = 22
isc_action_svc_trace_stop = 23
isc_action_svc_trace_suspend = 24
isc_action_svc_trace_resume = 25
isc_action_svc_trace_list = 26
isc_action_svc_set_mapping = 27
isc_action_svc_drop_mapping = 28
isc_action_svc_display_user_adm = 29
isc_action_svc_last = 30

# Service information items
isc_info_svc_svr_db_info = 50    # Retrieves the number of attachments and databases */
isc_info_svc_get_config = 53     # Retrieves the parameters and values for IB_CONFIG */
isc_info_svc_version = 54        # Retrieves the version of the services manager */
isc_info_svc_server_version = 55 # Retrieves the version of the Firebird server */
isc_info_svc_implementation = 56 # Retrieves the implementation of the Firebird server */
isc_info_svc_capabilities = 57   # Retrieves a bitmask representing the server's capabilities */
isc_info_svc_user_dbpath = 58    # Retrieves the path to the security database in use by the server */
isc_info_svc_get_env = 59        # Retrieves the setting of $FIREBIRD */
isc_info_svc_get_env_lock = 60   # Retrieves the setting of $FIREBIRD_LCK */
isc_info_svc_get_env_msg = 61    # Retrieves the setting of $FIREBIRD_MSG */
isc_info_svc_line = 62           # Retrieves 1 line of service output per call */
isc_info_svc_to_eof = 63         # Retrieves as much of the server output as will fit in the supplied buffer */
isc_info_svc_timeout = 64        # Sets / signifies a timeout value for reading service information */
isc_info_svc_limbo_trans = 66    # Retrieve the limbo transactions */
isc_info_svc_running = 67        # Checks to see if a service is running on an attachment */
isc_info_svc_get_users = 68      # Returns the user information from isc_action_svc_display_users */

# Parameters for isc_action_{add|del|mod|disp)_user
isc_spb_sec_userid = 5
isc_spb_sec_groupid = 6
isc_spb_sec_username = 7
isc_spb_sec_password = 8
isc_spb_sec_groupname = 9
isc_spb_sec_firstname = 10
isc_spb_sec_middlename = 11
isc_spb_sec_lastname = 12
isc_spb_sec_admin = 13

# Parameters for isc_action_svc_backup
isc_spb_bkp_file = 5
isc_spb_bkp_factor = 6
isc_spb_bkp_length = 7
isc_spb_bkp_ignore_checksums = 0x01
isc_spb_bkp_ignore_limbo = 0x02
isc_spb_bkp_metadata_only = 0x04
isc_spb_bkp_no_garbage_collect = 0x08
isc_spb_bkp_old_descriptions = 0x10
isc_spb_bkp_non_transportable = 0x20
isc_spb_bkp_convert = 0x40
isc_spb_bkp_expand = 0x80
isc_spb_bkp_no_triggers = 0x8000

# Parameters for isc_action_svc_properties
isc_spb_prp_page_buffers = 5
isc_spb_prp_sweep_interval = 6
isc_spb_prp_shutdown_db = 7
isc_spb_prp_deny_new_attachments = 9
isc_spb_prp_deny_new_transactions = 10
isc_spb_prp_reserve_space = 11
isc_spb_prp_write_mode = 12
isc_spb_prp_access_mode = 13
isc_spb_prp_set_sql_dialect = 14
isc_spb_prp_activate = 0x0100
isc_spb_prp_db_online = 0x0200
isc_spb_prp_force_shutdown = 41
isc_spb_prp_attachments_shutdown = 42
isc_spb_prp_transactions_shutdown = 43
isc_spb_prp_shutdown_mode = 44
isc_spb_prp_online_mode = 45

# Parameters for isc_spb_prp_shutdown_mode and isc_spb_prp_online_mode
isc_spb_prp_sm_normal = 0
isc_spb_prp_sm_multi = 1
isc_spb_prp_sm_single = 2
isc_spb_prp_sm_full = 3

# Parameters for isc_spb_prp_reserve_space
isc_spb_prp_res_use_full = 35
isc_spb_prp_res = 36

# Parameters for isc_spb_prp_write_mode
isc_spb_prp_wm_async = 37
isc_spb_prp_wm_sync = 38

# Parameters for isc_spb_prp_access_mode
isc_spb_prp_am_readonly = 39
isc_spb_prp_am_readwrite = 40

# Parameters for isc_action_svc_repair
isc_spb_rpr_commit_trans = 15
isc_spb_rpr_rollback_trans = 34
isc_spb_rpr_recover_two_phase = 17
isc_spb_tra_id = 18
isc_spb_single_tra_id = 19
isc_spb_multi_tra_id = 20
isc_spb_tra_state = 21
isc_spb_tra_state_limbo = 22
isc_spb_tra_state_commit = 23
isc_spb_tra_state_rollback = 24
isc_spb_tra_state_unknown = 25
isc_spb_tra_host_site = 26
isc_spb_tra_remote_site = 27
isc_spb_tra_db_path = 28
isc_spb_tra_advise = 29
isc_spb_tra_advise_commit = 30
isc_spb_tra_advise_rollback = 31
isc_spb_tra_advise_unknown = 33

isc_spb_rpr_validate_db = 0x01
isc_spb_rpr_sweep_db = 0x02
isc_spb_rpr_mend_db = 0x04
isc_spb_rpr_list_limbo_trans = 0x08
isc_spb_rpr_check_db = 0x10
isc_spb_rpr_ignore_checksum = 0x20
isc_spb_rpr_kill_shadows = 0x40
isc_spb_rpr_full = 0x80

# Parameters for isc_action_svc_restore
isc_spb_res_buffers = 9
isc_spb_res_page_size = 10
isc_spb_res_length = 11
isc_spb_res_access_mode = 12
isc_spb_res_fix_fss_data = 13
isc_spb_res_fix_fss_metadata = 14
isc_spb_res_metadata_only = 0x04
isc_spb_res_deactivate_idx = 0x0100
isc_spb_res_no_shadow = 0x0200
isc_spb_res_no_validity = 0x0400
isc_spb_res_one_at_a_time = 0x0800
isc_spb_res_replace = 0x1000
isc_spb_res_create = 0x2000
isc_spb_res_use_all_space = 0x4000

# Parameters for isc_spb_res_access_mode
isc_spb_res_am_readonly = isc_spb_prp_am_readonly
isc_spb_res_am_readwrite = isc_spb_prp_am_readwrite

# Parameters for isc_info_svc_svr_db_info
isc_spb_num_att = 5
isc_spb_num_db = 6

# Parameters for isc_info_svc_db_stats
isc_spb_sts_data_pages = 0x01
isc_spb_sts_db_log = 0x02
isc_spb_sts_hdr_pages = 0x04
isc_spb_sts_idx_pages = 0x08
isc_spb_sts_sys_relations = 0x10
isc_spb_sts_record_versions = 0x20
isc_spb_sts_table = 0x40
isc_spb_sts_nocreation = 0x80

# Parameters for isc_action_svc_nbak
isc_spb_nbk_level = 5
isc_spb_nbk_file = 6
isc_spb_nbk_direct = 7
isc_spb_nbk_no_triggers = 0x01

# trace
isc_spb_trc_id = 1
isc_spb_trc_name = 2
isc_spb_trc_cfg = 3

#-------------------

# STRING = c_char_p
# WSTRING = c_wchar_p

blb_got_eof = 0
blb_got_fragment = -1
blb_got_full_segment = 1
blb_seek_relative = 1
blb_seek_from_tail = 2

# Implementation codes
isc_info_db_impl_rdb_vms = 1
isc_info_db_impl_rdb_eln = 2
isc_info_db_impl_rdb_eln_dev = 3
isc_info_db_impl_rdb_vms_y = 4
isc_info_db_impl_rdb_eln_y = 5
isc_info_db_impl_jri = 6
isc_info_db_impl_jsv = 7
isc_info_db_impl_isc_apl_68K = 25
isc_info_db_impl_isc_vax_ultr = 26
isc_info_db_impl_isc_vms = 27
isc_info_db_impl_isc_sun_68k = 28
isc_info_db_impl_isc_os2 = 29
isc_info_db_impl_isc_sun4 = 30
isc_info_db_impl_isc_hp_ux = 31
isc_info_db_impl_isc_sun_386i = 32
isc_info_db_impl_isc_vms_orcl = 33
isc_info_db_impl_isc_mac_aux = 34
isc_info_db_impl_isc_rt_aix = 35
isc_info_db_impl_isc_mips_ult = 36
isc_info_db_impl_isc_xenix = 37
isc_info_db_impl_isc_dg = 38
isc_info_db_impl_isc_hp_mpexl = 39
isc_info_db_impl_isc_hp_ux68K = 40
isc_info_db_impl_isc_sgi = 41
isc_info_db_impl_isc_sco_unix = 42
isc_info_db_impl_isc_cray = 43
isc_info_db_impl_isc_imp = 44
isc_info_db_impl_isc_delta = 45
isc_info_db_impl_isc_next = 46
isc_info_db_impl_isc_dos = 47
isc_info_db_impl_m88K = 48
isc_info_db_impl_unixware = 49
isc_info_db_impl_isc_winnt_x86 = 50
isc_info_db_impl_isc_epson = 51
isc_info_db_impl_alpha_osf = 52
isc_info_db_impl_alpha_vms = 53
isc_info_db_impl_netware_386 = 54
isc_info_db_impl_win_only = 55
isc_info_db_impl_ncr_3000 = 56
isc_info_db_impl_winnt_ppc = 57
isc_info_db_impl_dg_x86 = 58
isc_info_db_impl_sco_ev = 59
isc_info_db_impl_i386 = 60
isc_info_db_impl_freebsd = 61
isc_info_db_impl_netbsd = 62
isc_info_db_impl_darwin_ppc = 63
isc_info_db_impl_sinixz = 64
isc_info_db_impl_linux_sparc = 65
isc_info_db_impl_linux_amd64 = 66
isc_info_db_impl_freebsd_amd64 = 67
isc_info_db_impl_winnt_amd64 = 68
isc_info_db_impl_linux_ppc = 69
isc_info_db_impl_darwin_x86 = 70
isc_info_db_impl_linux_mipsel = 71 # changed in 2.1, it was isc_info_db_impl_sun_amd64 in 2.0
# Added in FB 2.1
isc_info_db_impl_linux_mips = 72
isc_info_db_impl_darwin_x64 = 73
isc_info_db_impl_sun_amd64 = 74
isc_info_db_impl_linux_arm = 75
isc_info_db_impl_linux_ia64 = 76
isc_info_db_impl_darwin_ppc64 = 77
isc_info_db_impl_linux_s390x = 78
isc_info_db_impl_linux_s390 = 79
isc_info_db_impl_linux_sh = 80
isc_info_db_impl_linux_sheb = 81
# Added in FB 2.5
isc_info_db_impl_linux_hppa = 82
isc_info_db_impl_linux_alpha = 83
isc_info_db_impl_last_value = (isc_info_db_impl_linux_alpha + 1)

# Info DB provider
isc_info_db_code_rdb_eln = 1
isc_info_db_code_rdb_vms = 2
isc_info_db_code_interbase = 3
isc_info_db_code_firebird = 4
isc_info_db_code_last_value = (isc_info_db_code_firebird+1)

# Info db class
isc_info_db_class_access = 1
isc_info_db_class_y_valve = 2
isc_info_db_class_rem_int = 3
isc_info_db_class_rem_srvr = 4
isc_info_db_class_pipe_int = 7
isc_info_db_class_pipe_srvr = 8
isc_info_db_class_sam_int = 9
isc_info_db_class_sam_srvr = 10
isc_info_db_class_gateway = 11
isc_info_db_class_cache = 12
isc_info_db_class_classic_access = 13
isc_info_db_class_server_access = 14
isc_info_db_class_last_value = (isc_info_db_class_server_access+1)

# def fbclient_API(fb_library_name):
#     from fdb._ibase import ffi, lib
#     return lib

class fbclient_API(object):
    """Firebird Client API interface object. Loads Firebird Client Library and exposes
    API functions as member methods. Uses :ref:`ctypes <python:module-ctypes>` for bindings.
    """
    __all__ = ['ffi', 'BLOB_close', 'BLOB_display', 'BLOB_dump', 'BLOB_edit', 'BLOB_get', 'BLOB_load', 'BLOB_open', 'BLOB_put', 'BLOB_text_dump', 'BLOB_text_load', 'Bopen', 'fb_cancel_operation', 'fb_disconnect_transaction', 'fb_interpret', 'fb_print_blr', 'fb_shutdown', 'fb_shutdown_callback', 'fb_sqlstate', 'isc_add_user', 'isc_array_gen_sdl', 'isc_array_get_slice', 'isc_array_lookup_bounds', 'isc_array_lookup_desc', 'isc_array_put_slice', 'isc_array_set_desc', 'isc_attach_database', 'isc_baddress', 'isc_baddress_s', 'isc_blob_default_desc', 'isc_blob_gen_bpb', 'isc_blob_info', 'isc_blob_lookup_desc', 'isc_blob_set_desc', 'isc_cancel_blob', 'isc_cancel_events', 'isc_close', 'isc_close_blob', 'isc_commit_retaining', 'isc_commit_transaction', 'isc_compile_request', 'isc_compile_request2', 'isc_create_blob', 'isc_create_blob2', 'isc_create_database', 'isc_database_info', 'isc_declare', 'isc_decode_date', 'isc_decode_sql_date', 'isc_decode_sql_time', 'isc_decode_timestamp', 'isc_delete_user', 'isc_describe', 'isc_describe_bind', 'isc_detach_database', 'isc_drop_database', 'isc_dsql_alloc_statement2', 'isc_dsql_allocate_statement', 'isc_dsql_describe', 'isc_dsql_describe_bind', 'isc_dsql_exec_immed2', 'isc_dsql_exec_immed3_m', 'isc_dsql_execute', 'isc_dsql_execute2', 'isc_dsql_execute2_m', 'isc_dsql_execute_immediate', 'isc_dsql_execute_immediate_m', 'isc_dsql_execute_m', 'isc_dsql_fetch', 'isc_dsql_fetch_m', 'isc_dsql_finish', 'isc_dsql_free_statement', 'isc_dsql_insert', 'isc_dsql_insert_m', 'isc_dsql_prepare', 'isc_dsql_prepare_m', 'isc_dsql_release', 'isc_dsql_set_cursor_name', 'isc_dsql_sql_info', 'isc_embed_dsql_close', 'isc_embed_dsql_declare', 'isc_embed_dsql_describe', 'isc_embed_dsql_describe_bind', 'isc_embed_dsql_execute', 'isc_embed_dsql_execute2', 'isc_embed_dsql_execute_immed', 'isc_embed_dsql_fetch', 'isc_embed_dsql_fetch_a', 'isc_embed_dsql_insert', 'isc_embed_dsql_length', 'isc_embed_dsql_open', 'isc_embed_dsql_open2', 'isc_embed_dsql_prepare', 'isc_embed_dsql_release', 'isc_encode_date', 'isc_encode_sql_date', 'isc_encode_sql_time', 'isc_encode_timestamp', 'isc_event_block_a', 'isc_event_block_s', 'isc_event_counts', 'isc_execute', 'isc_execute_immediate', 'isc_fetch', 'isc_free', 'isc_ftof', 'isc_get_client_major_version', 'isc_get_client_minor_version', 'isc_get_client_version', 'isc_get_segment', 'isc_get_slice', 'isc_modify_dpb', 'isc_modify_user', 'isc_open', 'isc_open_blob', 'isc_open_blob2', 'isc_portable_integer', 'isc_prepare', 'isc_prepare_transaction', 'isc_prepare_transaction2', 'isc_print_blr', 'isc_print_sqlerror', 'isc_print_status', 'isc_put_segment', 'isc_put_slice', 'isc_qtoq', 'isc_que_events', 'isc_receive', 'isc_reconnect_transaction', 'isc_release_request', 'isc_request_info', 'isc_rollback_retaining', 'isc_rollback_transaction', 'isc_seek_blob', 'isc_send', 'isc_service_attach', 'isc_service_detach', 'isc_service_query', 'isc_service_start', 'isc_set_debug', 'isc_sql_interprete', 'isc_sqlcode', 'isc_sqlcode_s', 'isc_start_and_send', 'isc_start_multiple', 'isc_start_request', 'isc_transact_request', 'isc_transaction_info', 'isc_unwind_request', 'isc_vax_integer', 'isc_version', 'isc_vtof', 'isc_vtov', 'isc_wait_for_event']

    def __init__(self,*args, **kwargs):
        from fdb._ibase import ffi, lib
        self.lib = lib
        self.ffi = ffi

    def __getattr__(self, item):
        return self.lib.__getattr__(item)
#
#     def isc_event_block(self,event_buffer,result_buffer,*args):
#         # if len(args) > 15:
#         #     raise Exception("isc_event_block takes no more than 15 event names")
#         # newargs = list(self.P_isc_event_block_args)
#         # for x in args:
#         #     newargs.append(STRING)
#         # self.C_isc_event_block.argtypes = newargs
#         # result = self.C_isc_event_block(event_buffer,result_buffer,len(args),*args)
#         # return result
#         raise NotImplementedError
#
