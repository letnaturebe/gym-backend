from rest_framework.exceptions import APIException


class InvalidEndTime(APIException):
    status_code = 400
    default_detail = "수업 시작시간 < 종료시간"


class ExceedLessonTime(APIException):
    status_code = 400
    default_detail = "이미 진행한 수업 예약 불가"


class NotEnoughCredit(APIException):
    status_code = 400
    default_detail = "크레딧 부족"


class ExceedMaxCapacity(APIException):
    status_code = 400
    default_detail = "수용 가능 인원 초과"


class AlreadyRegistered(APIException):
    status_code = 400
    default_detail = "이미 등록한 예약"


class InvalidCancelDate(APIException):
    status_code = 400
    default_detail = "수업 당일 및 지나간 일자 취소 불가"


class AlreadyCanceled(APIException):
    status_code = 400
    default_detail = "이미 취소한 수업 예약"


class NotYourReservation(APIException):
    status_code = 403
    default_detail = "요청한 사용자와 예약자가 다름"


class InvalidReservationType(APIException):
    status_code = 400
    default_detail = "예약 취소건은 취소 불가"
