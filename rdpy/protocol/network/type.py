'''
@author: sylvain
'''

import struct
from copy import deepcopy
from StringIO import StringIO
from error import InvalidValue, InvalidType

def sizeof(element):
    '''
    byte size of type
    @param element: Type or Tuple(Type | Tuple,)
    @return: size of element in byte
    @raise InvalidType: if type is different than tuple of Type inheritance
    '''
    if isinstance(element, tuple):
        size = 0
        for i in element:
            size += sizeof(i)
        return size
    elif isinstance(element, Type):
        return element.__sizeof__()
    
    raise InvalidType("invalid type for sizeof")
            

class Type(object):
    '''
    root type
    '''
    def __init__(self, write_if = lambda:True, read_if = lambda:True):
        self._write_if = write_if
        self._read_if = read_if
        
    def write(self, s):
        '''
        interface definition of write function
        @param s: Stream which will be written
        '''
        if not self._write_if():
            return
        self.__write__(s)
    
    def read(self, s):
        '''
        interface definition of read value
        @param s: Stream
        @return: Type read from Stream s
        '''
        if not self._read_if():
            return
        self.__read__(s)
    
    def __sizeof__(self):
        '''
        return size of type use for sizeof function
        @return: size in byte of type
        '''
        pass
    
class ValueType(Type):
    '''
    type that wrap an inner type
    acces with value getter and setter
    value can be a callable which is call
    at each access of value
    '''
    def __init__(self, value, write_if = lambda:True, read_if = lambda:True):
        Type.__init__(self, write_if = write_if, read_if = read_if)
        self._value = None
        self.value = value
    
    def __getValue__(self):
        '''
        shortcut to access inner value
        call lambda value
        @return: inner value(python type value)
        '''
        return self._value()
    
    def __setValue__(self, value):
        '''
        setter of value wrap in lambda value
        @param value: new value encompass in valuetype object
        '''
        value_callable = lambda:value
        if callable(value):
            value_callable = value
            
        self._value = value_callable
    
    @property
    def value(self):
        '''
        shortcut to access inner value
        @return: inner value(python type value)
        '''
        return self.__getValue__()
    
    @value.setter
    def value(self, value):
        '''
        setter of value after check it
        @param value: new value encompass in simpletype object
        @raise InvalidValue: if value doesn't respect type range
        '''
        self.__setValue__(value)

class SimpleType(ValueType):
    '''
    simple type
    '''
    def __init__(self, structFormat, typeSize, signed, value, write_if = lambda:True, read_if = lambda:True):
        '''
        constructor of simple type
        @param structFormat: letter that represent type in struct package
        @param typeSize: size in byte of type
        @param signed: true if type represent a signed type
        @param value: value recorded in this object
        '''
        self._signed = signed
        self._typeSize = typeSize
        self._structFormat = structFormat
        ValueType.__init__(self, value, write_if = write_if, read_if = read_if)
        
    def __getValue__(self):
        '''
        shortcut to access inner value
        @return: inner value(python type value)
        @raise InvalidValue: if value doesn't respect type range
        '''
        value = ValueType.__getValue__(self)
        if not self.isInRange(value):
            raise InvalidValue("value is out of range for %s"%self.__class__)
        
        if self._signed:
            return value
        else:
            return value & self.mask()

    def __setValue__(self, value):
        '''
        setter of value after check it
        @param value: new value encompass in simpletype object
        @raise InvalidValue: if value doesn't respect type range
        '''
        #check static value range
        if not callable(value) and not self.isInRange(value):
            raise InvalidValue("value is out of range for %s"%self.__class__)
        
        ValueType.__setValue__(self, value)
            
    
    def __cmp__(self, other):
        '''
        compare inner value
        magic function of python use for any compare operators
        @param other: SimpleType value which will be compared with self value
        or try to construct same type as self around other value
        @return: python value compare
        '''
        if not isinstance(other, SimpleType):
            other = self.__class__(other)
        return self.value.__cmp__(other.value)
        
    def __write__(self, s):
        '''
        write value in stream s
        use struct package to pack value
        @param s: Stream which will be written
        '''
        s.write(struct.pack(self._structFormat, self.value))
        
    def __read__(self, s):
        '''
        read inner value from stream
        use struct package
        @param s: Stream
        '''
        self.value = struct.unpack(self._structFormat,s.read(self._typeSize))[0]
      
    def mask(self):
        '''
        compute bit mask for type
        because in python all numbers are int long or float
        '''
        if not self.__dict__.has_key("_mask"):
            mask = 0xff
            for i in range(1, self._typeSize):
                mask = mask << 8 | 0xff
            self._mask = mask
        return self._mask
    
    def isInRange(self, value):
        '''
        check if value is in mask range
        @param value: python value
        @return: true if value is in type range
        '''
        if self._signed:
            return not (value < -(self.mask() >> 1) or value > (self.mask() >> 1))
        else:
            return not (value < 0 or value > self.mask())
        
    def __sizeof__(self):
        '''
        return size of type
        @return: typeSize pass in constructor
        '''
        return self._typeSize
    
    def __invert__(self):
        '''
        implement not operator
        @return: __class__ value
        '''
        invert = ~self.value
        if not self._signed:
            invert &= self.mask()
        return self.__class__(invert)
    
    def __add__(self, other):
        '''
        implement addition operator
        @param other: SimpleType value or try to construct same type as self
        around other value
        @return: self.__class__ object with add result
        @raise InvalidValue: if new value is out of bound
        '''
        if not isinstance(other, SimpleType):
            other = self.__class__(other)
        return self.__class__(self.value.__add__(other.value))
    
    def __sub__(self, other):
        '''
        implement sub operator
        @param other: SimpleType value or try to construct same type as self
        around other value
        @return: self.__class__ object with sub result
        @raise InvalidValue: if new value is out of bound
        '''
        if not isinstance(other, SimpleType):
            other = self.__class__(other)
        return self.__class__(self.value.__sub__(other.value))
    
    def __and__(self, other):
        '''
        implement bitwise and operator
        @param other: SimpleType value or try to construct same type as self
        around other value
        @return: self.__class__ object with and result
        '''
        if not isinstance(other, SimpleType):
            other = self.__class__(other)
        return self.__class__(self.value.__and__(other.value))
    
    def __or__(self, other):
        '''
        implement bitwise and operator
        @param other: SimpleType value or try to construct same type as self
        around other value
        @return: self.__class__ object with or result
        '''
        if not isinstance(other, SimpleType):
            other = self.__class__(other)
        return self.__class__(self.value.__or__(other.value))
    
    def __lshift__(self, other):
        '''
        left shift operator
        @param other: python int
        @return: self.__class__ object with or result
        '''
        if not isinstance(other, SimpleType):
            other = self.__class__(other)
        return self.__class__(self.value.__lshift__(other.value))
    
    def __rshift__(self, other):
        '''
        left shift operator
        @param other: python int
        @return: self.__class__ object with or result
        '''
        if not isinstance(other, SimpleType):
            other = self.__class__(other)
        return self.__class__(self.value.__rshift__(other.value))
    
    def __hash__(self):
        '''
        hash function to treat simple type in hash collection
        @return: hash of inner value
        '''
        return hash(self.value)

        
class CompositeType(Type):
    '''
    keep ordering declaration of simple type
    in list and transparent for other type
    '''
    def __init__(self, write_if = lambda:True, read_if = lambda:True):
        '''
        init list of simple value
        '''
        Type.__init__(self, write_if = write_if, read_if = read_if)
        #list of ordoned type
        self._typeName = []
    
    def __setattr__(self, name, value):
        '''
        magic function to update type list
        @param name: name of new attribute
        @param value: value of new attribute
        '''
        if name[0] != '_' and (isinstance(value, Type) or isinstance(value, tuple)) and not name in self._typeName:
            self._typeName.append(name)
        self.__dict__[name] = value
            
    def __read__(self, s):
        '''
        call read on each ordered subtype 
        @param s: Stream
        '''
        for name in self._typeName:
            s.readType(self.__dict__[name])
            
    def __write__(self, s):
        '''
        call write on each ordered subtype
        @param s: Stream
        '''
        for name in self._typeName:
            s.writeType(self.__dict__[name])
            
    def __sizeof__(self):
        '''
        call sizeof on each subtype$
        @return: sum of sizeof of each public type attributes
        '''
        size = 0
        for name in self._typeName:
            size += sizeof(self.__dict__[name])
        return size

    def __eq__(self, other):
        '''
        compare each properties which are Type inheritance
        if one is different then not equal
        @param other: CompositeType
        @return: True if each subtype are equals
        '''
        if self._typeName != other._typeName:
            return False
        for name in self._typeName:
            if self.__dict__[name] != other.__dict__[name]:
                return False
        return True
    
    def __ne__(self, other):
        '''
        return not equal result operator
        @param other: CompositeType
        @return: False if each subtype are equals
        '''
        return not self.__eq__(other)

class UInt8(SimpleType):
    '''
    unsigned byte
    '''    
    def __init__(self, value = 0, write_if = lambda:True, read_if = lambda:True):
        SimpleType.__init__(self, "B", 1, False, value, write_if = write_if, read_if = read_if)

class SInt8(SimpleType):
    '''
    signed byte
    '''    
    def __init__(self, value = 0, write_if = lambda:True, read_if = lambda:True):
        SimpleType.__init__(self, "b", 1, True, value, write_if = write_if, read_if = read_if)
        
        
class UInt16Be(SimpleType):
    '''
    unsigned short with big endian representation
    @attention: inner value is in machine representation
    Big endian is just for read or write in stream
    '''
    def __init__(self, value = 0, write_if = lambda:True, read_if = lambda:True):
        SimpleType.__init__(self, ">H", 2, False, value, write_if = write_if, read_if = read_if)
        
class UInt16Le(SimpleType):
    '''
    unsigned short with little endian representation
    @attention: inner value is in machine representation
    Big endian is just for read or write in stream
    '''
    def __init__(self, value = 0, write_if = lambda:True, read_if = lambda:True):
        SimpleType.__init__(self, "<H", 2, False, value, write_if = write_if, read_if = read_if)
        
class UInt32Be(SimpleType):
    '''
    unsigned int with big endian representation
    @attention: inner value is in machine representation
    Big endian is just for read or write in stream
    '''
    def __init__(self, value = 0, write_if = lambda:True, read_if = lambda:True):
        SimpleType.__init__(self, ">I", 4, False, value, write_if = write_if, read_if = read_if)
        
class UInt32Le(SimpleType):
    '''
    unsigned int with little endian representation
    @attention: inner value is in machine representation
    Big endian is just for read or write in stream
    '''
    def __init__(self, value = 0, write_if = lambda:True, read_if = lambda:True):
        SimpleType.__init__(self, "<I", 4, False, value, write_if = write_if, read_if = read_if)
    
class SInt32Le(SimpleType):
    '''
    signed int with little endian representation
    @attention: inner value is in machine representation
    Big endian is just for read or write in stream
    '''
    def __init__(self, value = 0, write_if = lambda:True, read_if = lambda:True):
        SimpleType.__init__(self, "<I", 4, True, value, write_if = write_if, read_if = read_if)
        
class SInt32Be(SimpleType):
    '''
    signed int with big endian representation
    @attention: inner value is in machine representation
    Big endian is just for read or write in stream
    '''
    def __init__(self, value = 0, write_if = lambda:True, read_if = lambda:True):
        SimpleType.__init__(self, ">I", 4, True, value, write_if = write_if, read_if = read_if)
        
class UInt24Be(SimpleType):
    '''
    unsigned 24 bit int with big endian representation
    @attention: inner value is in machine representation
    Big endian is just for read or write in stream
    '''
    def __init__(self, value = 0, write_if = lambda:True, read_if = lambda:True):
        SimpleType.__init__(self, ">I", 3, False, value, write_if = write_if, read_if = read_if)
        
    def __write__(self, s):
        '''
        special write for a special type
        '''
        s.write(struct.pack(">I", self.value)[1:])
        
class UInt24Le(SimpleType):
    '''
    unsigned int with little endian representation
    @attention: inner value is in machine representation
    Big endian is just for read or write in stream
    '''
    def __init__(self, value = 0, write_if = lambda:True, read_if = lambda:True):
        SimpleType.__init__(self, "<I", 3, False, value, write_if = write_if, read_if = read_if)   
            
    def __write__(self, s):
        '''
        special write for a special type
        @param s: Stream
        '''
        #don't write first byte
        s.write(struct.pack("<I", self.value)[1:])
        
class String(ValueType):
    '''
    String network type
    '''
    def __init__(self, value = "", write_if = lambda:True, read_if = lambda:True):
        '''
        constructor with new string
        @param value: python string use for inner value
        '''
        ValueType.__init__(self, value, write_if = write_if, read_if = read_if)
        
    def __eq__(self, other):
        '''
        call raw compare value
        @param other: other String parameter
        @return: if two inner value are equals
        '''
        return self.value == other.value
    
    def __hash__(self):
        '''
        hash function to treat simple type in hash collection
        @return: hash of inner value
        '''
        return hash(self.value)
    
    def __str__(self):
        '''
        call when str function is call
        @return: inner python string
        '''
        return self.value
    
    def __write__(self, s):
        '''
        write the entire raw value
        @param s: Stream
        '''
        s.write(self.value)
    
    def __read__(self, s):
        '''
        read all stream if len of inner value is zero
        else read the len of inner string
        @param s: Stream
        '''
        if len(self.value) == 0:
            self.value = s.getvalue()
        else:
            self.value = s.read(len(self.value))
        
    def __sizeof__(self):
        '''
        return len of string
        @return: len of inner string
        '''
        return len(self.value)
    
class UniString(String):
    '''
    string with unicode representation
    '''
    def write(self, s):
        '''
        separate each char with null char 
        and end with double null char
        @param s: Stream
        '''
        for c in self.value:
            s.writeType(UInt8(ord(c)))
            s.writeType(UInt8(0))
        s.writeType(UInt16Le(0))
        
    def __sizeof__(self):
        '''
        return len of uni string
        @return: 2*len + 2
        '''
        return len(self.value) * 2 + 2
    

class Stream(StringIO):
    '''
    use string io inheritance
    but in future (for python 3)
    make your own stream class
    '''
    def dataLen(self):
        '''
        @return: not yet read length
        '''
        return self.len - self.pos
    
    def readLen(self):
        '''
        compute already read size
        @return: read size of stream
        '''
        return self.pos
    
    def readType(self, value):
        '''
        call specific read on type object
        or iterate over tuple elements
        @param value: (tuple | Type) object
        '''
        #read each tuple
        if isinstance(value, tuple):
            for element in value:
                self.readType(element)
            return
        value.read(self)
        
    def readNextType(self, t):
        '''
        read next type but didn't consume it
        @param t: Type element
        '''
        self.readType(t)
        self.pos -= sizeof(t)
    
    def writeType(self, value):
        '''
        call specific write on type object
        or iterate over tuple element
        @param value: (tuple | Type)
        '''
        #write each element of tuple
        if isinstance(value, tuple):
            for element in value:
                self.writeType(element)
            return
        value.write(self)

def CheckValueOnRead(cls):
    '''
    wrap read method of class
    to check value on read
    if new value is different from old value
    raise InvalidValue
    @param cls: class that inherit from Type
    '''
    oldRead = cls.read
    def read(self, s):
        old = deepcopy(self)
        oldRead(self, s)
        if self != old:
            raise InvalidValue("CheckValueOnRead %s != %s"%(self, old))
    cls.read = read
    return cls

def hexDump(src, length=16):
    '''
    print hex representation of sr
    @param src: string
    '''
    FILTER = ''.join([(len(repr(chr(x))) == 3) and chr(x) or '.' for x in range(256)])
    for c in xrange(0, len(src), length):
        chars = src[c:c+length]
        hexa = ' '.join(["%02x" % ord(x) for x in chars])
        printable = ''.join(["%s" % ((ord(x) <= 127 and FILTER[ord(x)]) or '.') for x in chars])
        print "%04x %-*s %s" % (c, length*3, hexa, printable)