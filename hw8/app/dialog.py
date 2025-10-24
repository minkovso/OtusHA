import logging
import os
import ulid
from concurrent import futures
import grpc
from proto import dialog_pb2
from proto import dialog_pb2_grpc
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.auth import PasswordAuthenticator
from couchbase.options import QueryOptions

logger = logging.getLogger('dialog')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s [request_id=%(request_id)s] %(levelname)s: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class RequestIdInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        md = dict(handler_call_details.invocation_metadata or [])
        request_id = md.get('request_id', str(ulid.new()))
        extra = {'request_id': request_id}
        handler = continuation(handler_call_details)
        def behavior(request, context):
            logger.info('gRPC request in', extra=extra)
            resp = handler.unary_unary(request, context)
            logger.info('gRPC response out', extra=extra)
            return resp
        return grpc.unary_unary_rpc_method_handler(
            behavior,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

class DialogServiceServicer(dialog_pb2_grpc.DialogServiceServicer):
    @staticmethod
    def get_couch_conn():
        cluster = Cluster(
            os.getenv('COUCH_HOST'),
            ClusterOptions(PasswordAuthenticator(os.getenv('COUCH_USER'), os.getenv('COUCH_PASSWORD')))
        )
        bucket = cluster.bucket(os.getenv('COUCH_BUCKET'))
        return bucket

    def Send(self, request, context):
        bucket = self.get_couch_conn()
        scope = bucket.scope('prod')
        coll = scope.collection('messages')
        dialog_id = f'{min((request.friend_id, request.user_id))}_{max((request.friend_id, request.user_id))}'
        message_id = ulid.new()
        doc_id = f'{dialog_id}:{message_id}'
        doc = {
            'from': request.user_id,
            'to': request.friend_id,
            'text': request.text,
            'created_at': message_id.timestamp().datetime.replace(tzinfo=None, microsecond=0).isoformat()
        }
        try:
            coll.insert(doc_id, doc)
            return dialog_pb2.Ack(ok=True)
        except Exception:
            return dialog_pb2.Ack(ok=False)

    def List(self, request, context):
        bucket = self.get_couch_conn()
        scope = bucket.scope('prod')
        query = '''
            SELECT text
            FROM `prod`.`prod`.`messages`
            WHERE (`from` = $user_id AND `to` = $friend_id)
               OR (`from` = $friend_id AND `to` = $user_id) \
        '''
        rows = scope.query(
            query,
            QueryOptions(named_parameters={'user_id': request.user_id, 'friend_id': request.friend_id})
        )
        messages = []
        for row in rows:
            message = dialog_pb2.Message(
                user_id=request.user_id,
                friend_id=request.friend_id,
                text=row['text'],
            )
            messages.append(message)
        return dialog_pb2.Messages(items=messages)

def main():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=8),
        interceptors=[RequestIdInterceptor()],
    )
    dialog_pb2_grpc.add_DialogServiceServicer_to_server(DialogServiceServicer(), server)
    port = os.environ.get('DIALOG_PORT')
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    main()
