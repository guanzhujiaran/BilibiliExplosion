# Generated by the Protocol Buffers compiler. DO NOT EDIT!
# source: bilibili/dynamic/interfaces/feed/v1/api.proto
# plugin: grpclib.plugin.main
import abc
import typing

import grpclib.const
import grpclib.client
if typing.TYPE_CHECKING:
    import grpclib.server

import bilibili.dynamic.common.dynamic_pb2
import bilibili.dynamic.interfaces.feed.v1.api_pb2


class FeedBase(abc.ABC):

    @abc.abstractmethod
    async def CreateInitCheck(self, stream: 'grpclib.server.Stream[bilibili.dynamic.interfaces.feed.v1.api_pb2.CreateInitCheckReq, bilibili.dynamic.common.dynamic_pb2.CreateCheckResp]') -> None:
        pass

    @abc.abstractmethod
    async def SubmitCheck(self, stream: 'grpclib.server.Stream[bilibili.dynamic.interfaces.feed.v1.api_pb2.SubmitCheckReq, bilibili.dynamic.interfaces.feed.v1.api_pb2.SubmitCheckRsp]') -> None:
        pass

    @abc.abstractmethod
    async def CreateDyn(self, stream: 'grpclib.server.Stream[bilibili.dynamic.interfaces.feed.v1.api_pb2.CreateDynReq, bilibili.dynamic.common.dynamic_pb2.CreateResp]') -> None:
        pass

    @abc.abstractmethod
    async def GetUidByName(self, stream: 'grpclib.server.Stream[bilibili.dynamic.common.dynamic_pb2.GetUidByNameReq, bilibili.dynamic.common.dynamic_pb2.GetUidByNameRsp]') -> None:
        pass

    @abc.abstractmethod
    async def AtList(self, stream: 'grpclib.server.Stream[bilibili.dynamic.common.dynamic_pb2.AtListReq, bilibili.dynamic.common.dynamic_pb2.AtListRsp]') -> None:
        pass

    @abc.abstractmethod
    async def AtSearch(self, stream: 'grpclib.server.Stream[bilibili.dynamic.common.dynamic_pb2.AtSearchReq, bilibili.dynamic.common.dynamic_pb2.AtListRsp]') -> None:
        pass

    @abc.abstractmethod
    async def ReserveButtonClick(self, stream: 'grpclib.server.Stream[bilibili.dynamic.interfaces.feed.v1.api_pb2.ReserveButtonClickReq, bilibili.dynamic.interfaces.feed.v1.api_pb2.ReserveButtonClickResp]') -> None:
        pass

    @abc.abstractmethod
    async def CreatePlusButtonClick(self, stream: 'grpclib.server.Stream[bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePlusButtonClickReq, bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePlusButtonClickRsp]') -> None:
        pass

    @abc.abstractmethod
    async def HotSearch(self, stream: 'grpclib.server.Stream[bilibili.dynamic.interfaces.feed.v1.api_pb2.HotSearchReq, bilibili.dynamic.interfaces.feed.v1.api_pb2.HotSearchRsp]') -> None:
        pass

    @abc.abstractmethod
    async def Suggest(self, stream: 'grpclib.server.Stream[bilibili.dynamic.interfaces.feed.v1.api_pb2.SuggestReq, bilibili.dynamic.interfaces.feed.v1.api_pb2.SuggestRsp]') -> None:
        pass

    @abc.abstractmethod
    async def DynamicButtonClick(self, stream: 'grpclib.server.Stream[bilibili.dynamic.interfaces.feed.v1.api_pb2.DynamicButtonClickReq, bilibili.dynamic.interfaces.feed.v1.api_pb2.DynamicButtonClickRsp]') -> None:
        pass

    @abc.abstractmethod
    async def CreatePermissionButtonClick(self, stream: 'grpclib.server.Stream[bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePermissionButtonClickReq, bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePermissionButtonClickRsp]') -> None:
        pass

    @abc.abstractmethod
    async def CreatePageInfos(self, stream: 'grpclib.server.Stream[bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePageInfosReq, bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePageInfosRsp]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/bilibili.main.dynamic.feed.v1.Feed/CreateInitCheck': grpclib.const.Handler(
                self.CreateInitCheck,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.CreateInitCheckReq,
                bilibili.dynamic.common.dynamic_pb2.CreateCheckResp,
            ),
            '/bilibili.main.dynamic.feed.v1.Feed/SubmitCheck': grpclib.const.Handler(
                self.SubmitCheck,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.SubmitCheckReq,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.SubmitCheckRsp,
            ),
            '/bilibili.main.dynamic.feed.v1.Feed/CreateDyn': grpclib.const.Handler(
                self.CreateDyn,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.CreateDynReq,
                bilibili.dynamic.common.dynamic_pb2.CreateResp,
            ),
            '/bilibili.main.dynamic.feed.v1.Feed/GetUidByName': grpclib.const.Handler(
                self.GetUidByName,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.dynamic.common.dynamic_pb2.GetUidByNameReq,
                bilibili.dynamic.common.dynamic_pb2.GetUidByNameRsp,
            ),
            '/bilibili.main.dynamic.feed.v1.Feed/AtList': grpclib.const.Handler(
                self.AtList,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.dynamic.common.dynamic_pb2.AtListReq,
                bilibili.dynamic.common.dynamic_pb2.AtListRsp,
            ),
            '/bilibili.main.dynamic.feed.v1.Feed/AtSearch': grpclib.const.Handler(
                self.AtSearch,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.dynamic.common.dynamic_pb2.AtSearchReq,
                bilibili.dynamic.common.dynamic_pb2.AtListRsp,
            ),
            '/bilibili.main.dynamic.feed.v1.Feed/ReserveButtonClick': grpclib.const.Handler(
                self.ReserveButtonClick,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.ReserveButtonClickReq,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.ReserveButtonClickResp,
            ),
            '/bilibili.main.dynamic.feed.v1.Feed/CreatePlusButtonClick': grpclib.const.Handler(
                self.CreatePlusButtonClick,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePlusButtonClickReq,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePlusButtonClickRsp,
            ),
            '/bilibili.main.dynamic.feed.v1.Feed/HotSearch': grpclib.const.Handler(
                self.HotSearch,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.HotSearchReq,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.HotSearchRsp,
            ),
            '/bilibili.main.dynamic.feed.v1.Feed/Suggest': grpclib.const.Handler(
                self.Suggest,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.SuggestReq,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.SuggestRsp,
            ),
            '/bilibili.main.dynamic.feed.v1.Feed/DynamicButtonClick': grpclib.const.Handler(
                self.DynamicButtonClick,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.DynamicButtonClickReq,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.DynamicButtonClickRsp,
            ),
            '/bilibili.main.dynamic.feed.v1.Feed/CreatePermissionButtonClick': grpclib.const.Handler(
                self.CreatePermissionButtonClick,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePermissionButtonClickReq,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePermissionButtonClickRsp,
            ),
            '/bilibili.main.dynamic.feed.v1.Feed/CreatePageInfos': grpclib.const.Handler(
                self.CreatePageInfos,
                grpclib.const.Cardinality.UNARY_UNARY,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePageInfosReq,
                bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePageInfosRsp,
            ),
        }


class FeedStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.CreateInitCheck = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.main.dynamic.feed.v1.Feed/CreateInitCheck',
            bilibili.dynamic.interfaces.feed.v1.api_pb2.CreateInitCheckReq,
            bilibili.dynamic.common.dynamic_pb2.CreateCheckResp,
        )
        self.SubmitCheck = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.main.dynamic.feed.v1.Feed/SubmitCheck',
            bilibili.dynamic.interfaces.feed.v1.api_pb2.SubmitCheckReq,
            bilibili.dynamic.interfaces.feed.v1.api_pb2.SubmitCheckRsp,
        )
        self.CreateDyn = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.main.dynamic.feed.v1.Feed/CreateDyn',
            bilibili.dynamic.interfaces.feed.v1.api_pb2.CreateDynReq,
            bilibili.dynamic.common.dynamic_pb2.CreateResp,
        )
        self.GetUidByName = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.main.dynamic.feed.v1.Feed/GetUidByName',
            bilibili.dynamic.common.dynamic_pb2.GetUidByNameReq,
            bilibili.dynamic.common.dynamic_pb2.GetUidByNameRsp,
        )
        self.AtList = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.main.dynamic.feed.v1.Feed/AtList',
            bilibili.dynamic.common.dynamic_pb2.AtListReq,
            bilibili.dynamic.common.dynamic_pb2.AtListRsp,
        )
        self.AtSearch = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.main.dynamic.feed.v1.Feed/AtSearch',
            bilibili.dynamic.common.dynamic_pb2.AtSearchReq,
            bilibili.dynamic.common.dynamic_pb2.AtListRsp,
        )
        self.ReserveButtonClick = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.main.dynamic.feed.v1.Feed/ReserveButtonClick',
            bilibili.dynamic.interfaces.feed.v1.api_pb2.ReserveButtonClickReq,
            bilibili.dynamic.interfaces.feed.v1.api_pb2.ReserveButtonClickResp,
        )
        self.CreatePlusButtonClick = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.main.dynamic.feed.v1.Feed/CreatePlusButtonClick',
            bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePlusButtonClickReq,
            bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePlusButtonClickRsp,
        )
        self.HotSearch = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.main.dynamic.feed.v1.Feed/HotSearch',
            bilibili.dynamic.interfaces.feed.v1.api_pb2.HotSearchReq,
            bilibili.dynamic.interfaces.feed.v1.api_pb2.HotSearchRsp,
        )
        self.Suggest = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.main.dynamic.feed.v1.Feed/Suggest',
            bilibili.dynamic.interfaces.feed.v1.api_pb2.SuggestReq,
            bilibili.dynamic.interfaces.feed.v1.api_pb2.SuggestRsp,
        )
        self.DynamicButtonClick = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.main.dynamic.feed.v1.Feed/DynamicButtonClick',
            bilibili.dynamic.interfaces.feed.v1.api_pb2.DynamicButtonClickReq,
            bilibili.dynamic.interfaces.feed.v1.api_pb2.DynamicButtonClickRsp,
        )
        self.CreatePermissionButtonClick = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.main.dynamic.feed.v1.Feed/CreatePermissionButtonClick',
            bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePermissionButtonClickReq,
            bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePermissionButtonClickRsp,
        )
        self.CreatePageInfos = grpclib.client.UnaryUnaryMethod(
            channel,
            '/bilibili.main.dynamic.feed.v1.Feed/CreatePageInfos',
            bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePageInfosReq,
            bilibili.dynamic.interfaces.feed.v1.api_pb2.CreatePageInfosRsp,
        )
