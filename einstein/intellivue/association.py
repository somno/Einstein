from scapy.all import *

from .common import *

"""
The LI field contains the length of the appended data (including all presentation data). The length
encoding uses the following rules:
* If the length is smaller or equal 254 bytes, LI is one byte containing the actual length.
* If the length is greater than 254 bytes, LI is three bytes, the first being 0xff, the following two bytes
containing the actual length.
Examples:
L = 15 is encoded as 0x0f
L = 256 is encoded as {0xff,0x01,0x00}
"""
class LIField(Field):
    def i2m(self, pkt, x):
        if x is None:
            x = len(pkt.payload)
        return x

    def addfield(self, pkt, s, val):
        val = self.i2m(pkt, val)
        if val < 255:
            b = struct.pack("B", val)
        else:
            b = '\xff' + struct.pack("!H", val)
        return s + b

    def getfield(self, pkt, s):
        if s[0] == '\xff':
            return s[3:], self.m2i(pkt, struct.unpack("!H", s[1:3])[0])
        else:
            return s[1:], self.m2i(pkt, struct.unpack("B", s[:1])[0])


CN_SPDU_SI = 0x0D  # PIPG-67 "CN_SPDU_SI: A Session Connect header. The message contains an Association Request"
AC_SPDU_SI = 0x0E  # PIPG-67 "AC_SPDU_SI: A Session Accept header. The message contains an Association Response, indicating that the association has been established."
RF_SPDU_SI = 0x0C  # PIPG-67 "RF_SPDU_SI: A Session Refuse header. An association could not be established."
FN_SPDU_SI = 0x09  # PIPG-67 "FN_SPDU_SI: A Session Finish header. The message contains a Release Request, indicating that the association should be terminated."
DN_SPDU_SI = 0x0A  # PIPG-67 "DN_SPDU_SI: A Session Disconnect header. The message contains a Release Response, indicating that the association has been terminated."
AB_SPDU_SI = 0x19  # PIPG-67 "AB_SPDU_SI: A Session Abort header. The message contains an Abort message, indicating the immediate termination of the association."


def SessionHeaderTypeField(name, default):  # PIPG-67
    enum = {
        CN_SPDU_SI: "CN_SPDU_SI",
        AC_SPDU_SI: "AC_SPDU_SI",
        RF_SPDU_SI: "RF_SPDU_SI",
        FN_SPDU_SI: "FN_SPDU_SI",
        DN_SPDU_SI: "DN_SPDU_SI",
        AB_SPDU_SI: "AB_SPDU_SI",
    }
    return ByteEnumField(name, default, enum)


class SessionHeader(Packet):
    name = "SessionHeader"
    fields_desc = [
        SessionHeaderTypeField("type", 0),
        LIField("length", None),
    ]


ASSOC_REQ_SESSION_DATA = "\x05\x08\x13\x01\x00\x16\x01\x02\x80\x00\x14\x02\x00\x02"


class AssocReqSessionData(Packet):
    name = "AssocReqSessionData"
    fields_desc = [
        StrFixedLenField("unknown", ASSOC_REQ_SESSION_DATA, length=len(ASSOC_REQ_SESSION_DATA)),  # Couldn't find a definition in the PIPG, this is copied from the example on page 298
    ]

class AssocReqPresentationHeaderHeader(Packet):  # Split AssocReqPresentationHeader because LIField is *everything* after, not just packet payload length
    name = "AssocReqPresentationHeaderHeader"
    fields_desc = [
        # Couldn't find a definition in the PIPG, this is copied from the example on page 298
        XByteField("prefix", 0xc1),
        LIField("LI", None),
    ]


ASSOC_REQ_PRESENTATION_HEADER_DATA = "\x31\x80\xA0\x80\x80\x01\x01\x00\x00\xA2\x80\xA0\x03\x00\x00\x01\xA4\x80\x30\x80\x02\x01\x01\x06\x04\x52\x01\x00\x01\x30\x80\x06\x02\x51\x01\x00\x00\x00\x00\x30\x80\x02\x01\x02\x06\x0C\x2A\x86\x48\xCE\x14\x02\x01\x00\x00\x00\x01\x01\x30\x80\x06\x0C\x2A\x86\x48\xCE\x14\x02\x01\x00\x00\x00\x02\x01\x00\x00\x00\x00\x00\x00\x61\x80\x30\x80\x02\x01\x01\xA0\x80\x60\x80\xA1\x80\x06\x0C\x2A\x86\x48\xCE\x14\x02\x01\x00\x00\x00\x03\x01\x00\x00\xBE\x80\x28\x80\x06\x0C\x2A\x86\x48\xCE\x14\x02\x01\x00\x00\x00\x01\x01\x02\x01\x02\x81"


class AssocReqPresentationHeaderData(Packet):
    name = "AssocReqPresentationHeaderData"
    fields_desc = [
        StrFixedLenField("unknown", ASSOC_REQ_PRESENTATION_HEADER_DATA, length=len(ASSOC_REQ_PRESENTATION_HEADER_DATA)),  # PIPG-298
    ]



"""
The ASNLength contains the length of the MDSEUserInfoStd. It uses the following encoding rules:
- if the length is less or equal to 127, ASNLength is one byte, containing the actual length.
- if the length is greater than 127, ASNLength is several bytes long. The most significant bit (bit 0) of the first byte is set to 1, the bits 1 to 7 indicate the number of bytes which are appended to encode the actual length.
"""
class ASNLengthField(FieldLenField):  # PIPG-68

    def addfield(self, pkt, s, val):
        val = self.i2m(pkt, val)
        if val < 128:
            b = struct.pack("B", val)
        else:
            raise NotImplementedError
        return s + b

    def getfield(self, pkt, s):
        v = struct.unpack("B", s[0])[0]
        if v & (1<<7):
            v &= ~(1<<7)
            raise NotImplementedError
        else:
            return s[1:], self.m2i(pkt, v)


MDDL_VERSION1 = 0x80000000  # PIPG-68
NOMEN_VERSION = 0x40000000  # PIPG-68
SYST_CLIENT = 0x80000000  # PIPG-69
SYST_SERVER = 0x00800000  # PIPG-69
HOT_START = 0x80000000
WARM_START = 0x40000000
COLD_START = 0x20000000

class MDSEUserInfoStd(Packet):  # PIPG-68
    name = "MDSEUserInfoStd"
    fields_desc = [
        XIntField("protocol_version", MDDL_VERSION1),
        XIntField("nomenclature_version", NOMEN_VERSION),
        XIntField("functional_units", None),
        XIntField("system_type", SYST_CLIENT),
        XIntField("startup_mode", WARM_START),
        PacketField("option_list", AttributeList(), AttributeList),
        PacketField("supported_aprofiles", AttributeList(), AttributeList),
    ]


class AssocReqUserData(Packet): # PIPG-65
    name = "AssocReqUserData"
    fields_desc = [
        ASNLengthField("ASNLength", None, length_of="MDSEUserInfoStd"),
        PacketField("MDSEUserInfoStd", MDSEUserInfoStd(), MDSEUserInfoStd),
    ]


POLL_PROFILE_REV_0 = 0x80000000  # PIPG-69


PollProfileOptionsField = XIntField  # PIPG-70 TODO Use some kind of flag field


P_OPT_DYN_CREATE_OBJECTS = 0x40000000
P_OPT_DYN_DELETE_OBJECTS = 0x20000000


class PollProfileSupport(Packet):  # PIPG-69
    name = "PollProfileSupport"
    fields_desc = [
        XIntField("poll_profile_revision", POLL_PROFILE_REV_0),
        RelativeTimeField("min_poll_period", 2500),  # Experimental default
        IntField("max_mtu_rx", 2500),  # Experimental default
        IntField("max_mtu_tx", 1000),  # Experimental default
        XIntField("max_bw_tx", 0xffffffff),  # The IntelliVue monitor fills in the maximum transmit bandwidth it uses, the value 0xffffffff indicates that no estimation is possible (this is the default).
        PollProfileOptionsField("options", P_OPT_DYN_CREATE_OBJECTS | P_OPT_DYN_DELETE_OBJECTS),
        PacketField("optional_packages", AttributeList(), AttributeList),
    ]


POLL_EXT_PERIOD_NU_1SEC = 0x80000000
POLL_EXT_PERIOD_NU_AVG_12SEC = 0x40000000
POLL_EXT_PERIOD_NU_AVG_60SEC = 0x20000000
POLL_EXT_PERIOD_NU_AVG_300SEC = 0x10000000
POLL_EXT_PERIOD_RTSA = 0x08000000
POLL_EXT_ENUM = 0x04000000
POLL_EXT_NU_PRIO_LIST = 0x02000000
POLL_EXT_DYN_MODALITIES = 0x01000000


PollProfileExtOptionsField = XIntField  # PIPG-71 TODO Use some kind of flag field


class PollProfileExt(Packet):  # PIPG-71
    name = "PollProfileExt"
    fields_desc = [
        PollProfileExtOptionsField("options", None),
        PacketField("ext_attr", AttributeList(), AttributeList),  # PIPG-72 "The ext_attr AttributeList is reserved for future extensions."
    ]


ASSOC_REQ_PRESENTATION_TRAILER = "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"


class AssocReqPresentationTrailer(Packet):
    name = "AssocReqPresentationTrailer"
    fields_desc = [
        StrField("unknown", ASSOC_REQ_PRESENTATION_TRAILER),  # PIPG-298
    ]


def makeAssociationRequest():
    packet = SessionHeader(type=CN_SPDU_SI) / AssocReqSessionData() / AssocReqPresentationHeaderHeader() / AssocReqPresentationHeaderData() / AssocReqUserData() / AssocReqPresentationTrailer()
    return raw(packet)


ReleaseRequest = "\x09\x18\xC1\x16\x61\x80\x30\x80\x02\x01\x01\xA0\x80\x62\x80\x80\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # PIPG-301
