import modelerpy  # type: ignore[import-untyped]
import pandas as pd
import re

# 読み込むログファイルのパス
FILE_1 = r"/usr/IBM/SPSS/ModelerServer/19.0/log/server_logging.log"

# ログ行をパースする正規表現
# 形式: 日時  プロセスID スレッドID ログレベル  [コンポーネント] モジュール メッセージ
LOG_PATTERN = re.compile(
    r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d+)'  # datetime, millisecond
    r'\s+(\d+)'                                          # process_id
    r'\s+(0x[0-9a-fA-F]+)'                              # thread_id
    r'\s+(\w+)'                                          # log_level
    r'\s+\[([^\]]+)\]'                                   # component
    r'\s+(\S+)'                                          # module
    r'\s+(.*)'                                           # message
)

# メッセージID と テキストを分離する正規表現
# 形式例: "AEQMC0075I: Accepted connection from ..."
MSG_SPLIT_PATTERN = re.compile(r'^([A-Z0-9]+):\s*(.*)', re.DOTALL)

# AEQMC0007I メッセージからセッション開始情報を抽出
# 例: "Session 25692 (dsuser1@::ffff:192.168.0.1.:50480) started"
SESSION_START_PATTERN = re.compile(r'Session\s+(\d+)\s+\(([^@]+)@.*\)\s+started', re.IGNORECASE)

# AEQMC0032I メッセージからセッション終了情報を抽出
# 例: "Session 25692 ended"
SESSION_END_PATTERN = re.compile(r'Session\s+(\d+)\s+ended', re.IGNORECASE)

# メッセージからユーザー名を抽出する正規表現
# 対象パターン例:
#   "Login succeeded for user: dsuser1"
#   "User name: dsuser1"
USER_PATTERN = re.compile(r'(?:for user|User name):\s*(\S+)', re.IGNORECASE)


def parse_log_lines(filepath):
    """ログファイルを読み込み、パース済みのレコードリストを返す"""
    records = []
    with open(filepath, encoding='utf-8-sig') as f:
        for line in f:
            line = line.rstrip('\n')
            m = LOG_PATTERN.match(line)
            if m:
                msg = m.group(8)
                ms = MSG_SPLIT_PATTERN.match(msg)
                msg_id = ms.group(1) if ms else None
                msg_text = ms.group(2) if ms else msg
                u = USER_PATTERN.search(msg)
                records.append({
                    'datetime': m.group(1),
                    'millisecond': int(m.group(2)),
                    'process_id': int(m.group(3)),
                    'thread_id': m.group(4),
                    'log_level': m.group(5),
                    'component': m.group(6),
                    'module': m.group(7),
                    'message_id': msg_id,
                    'message': msg_text,
                    'user_name': u.group(1) if u else None,
                    'source_file': filepath,
                })
            else:
                # パターンに合わない行（継続行など）は raw_line として格納
                records.append({
                    'datetime': None,
                    'millisecond': None,
                    'process_id': None,
                    'thread_id': None,
                    'log_level': None,
                    'component': None,
                    'module': None,
                    'message_id': None,
                    'message': line,
                    'user_name': None,
                    'source_file': filepath,
                })
    return records


if modelerpy.isComputeDataModelOnly():
    # --- データモデルのみを計算するフェーズ ---
    outputDataModel = modelerpy.DataModel([
        modelerpy.Field('datetime', 'timestamp', 'continuous'),
        modelerpy.Field('millisecond', 'integer', 'continuous'),
        modelerpy.Field('process_id', 'integer', 'continuous'),
        modelerpy.Field('thread_id', 'string', 'nominal'),
        modelerpy.Field('log_level', 'string', 'nominal'),
        modelerpy.Field('component', 'string', 'nominal'),
        modelerpy.Field('module', 'string', 'nominal'),
        modelerpy.Field('message_id', 'string', 'nominal'),
        modelerpy.Field('message', 'string', 'nominal'),
        modelerpy.Field('user_name', 'string', 'nominal'),
        modelerpy.Field('source_file', 'string', 'nominal'),
    ])
    modelerpy.setOutputDataModel(outputDataModel)

else:
    # --- 実データを計算するフェーズ ---
    records_1 = parse_log_lines(FILE_1)

    all_records = records_1

    outputData = pd.DataFrame(all_records, columns=pd.Index([
        'datetime', 'millisecond', 'process_id', 'thread_id',
        'log_level', 'component', 'module',
        'message_id', 'message', 'user_name', 'source_file',
    ]))

    # datetime列をdatetime型に変換
    outputData['datetime'] = pd.to_datetime(outputData['datetime'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    # None の整数列は -1 で埋める（integer 型を維持するため）
    outputData['millisecond'] = outputData['millisecond'].fillna(-1).astype(int)
    outputData['process_id'] = outputData['process_id'].fillna(-1).astype(int)

    # セッションの開始・終了を時系列で追跡
    # session_timeline: list of (datetime, process_id, event_type, username)
    # event_type: 'start' or 'end'
    session_timeline: list[tuple] = []  # type: ignore[type-arg]

    for row in outputData.itertuples():
        msg_id = getattr(row, 'message_id', None)
        msg = getattr(row, 'message', None)
        dt = getattr(row, 'datetime', None)

        if msg is not None and isinstance(msg, str) and dt is not None and not pd.isna(dt):
            # セッション開始を検出
            if msg_id == 'AEQMC0007I':
                sess_start = SESSION_START_PATTERN.search(msg)
                if sess_start:
                    session_pid = int(sess_start.group(1))
                    username = sess_start.group(2)
                    session_timeline.append((pd.Timestamp(dt), session_pid, 'start', username))

            # セッション終了を検出
            elif msg_id == 'AEQMC0032I':
                sess_end = SESSION_END_PATTERN.search(msg)
                if sess_end:
                    session_pid = int(sess_end.group(1))
                    session_timeline.append((pd.Timestamp(dt), session_pid, 'end', None))

    # タイムラインを時刻順にソート
    session_timeline.sort(key=lambda x: x[0])

    # 各レコードに対して、その時点で有効なセッションのユーザー名を割り当てる
    def fill_user_name(row: pd.Series) -> str | None:  # type: ignore[type-arg]
        user = row['user_name']
        # type: ignore を使用してpandasの型チェックを回避
        if user is not None and not pd.isna(user):  # type: ignore[arg-type]
            return str(user)

        pid = row['process_id']
        dt = row['datetime']

        if not isinstance(pid, int) or dt is None or pd.isna(dt):  # type: ignore[arg-type]
            return None

        # このレコードの時刻より前のイベントを逆順で探索
        current_user: str | None = None
        for event_dt, event_pid, event_type, event_user in reversed(session_timeline):
            if event_dt > dt:
                continue  # このイベントはレコードより後なのでスキップ

            if event_pid == pid:
                if event_type == 'start':
                    current_user = event_user
                    break
                elif event_type == 'end':
                    # セッション終了後なので、このプロセスIDは無効
                    break

        return current_user

    outputData['user_name'] = outputData.apply(fill_user_name, axis=1)  # type: ignore[arg-type]

    modelerpy.writePandasDataframe(outputData)
