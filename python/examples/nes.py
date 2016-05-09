# Copyright (c) 2015-2016 Vector 35 LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

from binaryninja import *
import struct
import traceback
import os

InstructionNames = [
	"brk", "ora", None, None, None, "ora", "asl", None, # 0x00
	"php", "ora", "asl@", None, None, "ora", "asl", None, # 0x08
	"bpl", "ora", None, None, None, "ora", "asl", None, # 0x10
	"clc", "ora", None, None, None, "ora", "asl", None, # 0x18
	"jsr", "and", None, None, "bit", "and", "rol", None, # 0x20
	"plp", "and", "rol@", None, "bit", "and", "rol", None, # 0x28
	"bmi", "and", None, None, None, "and", "rol", None, # 0x30
	"sec", "and", None, None, None, "and", "rol", None, # 0x38
	"rti", "eor", None, None, None, "eor", "lsr", None, # 0x40
	"pha", "eor", "lsr@", None, "jmp", "eor", "lsr", None, # 0x48
	"bvc", "eor", None, None, None, "eor", "lsr", None, # 0x50
	"cli", "eor", None, None, None, "eor", "lsr", None, # 0x58
	"rts", "adc", None, None, None, "adc", "ror", None, # 0x60
	"pla", "adc", "ror@", None, "jmp", "adc", "ror", None, # 0x68
	"bvs", "adc", None, None, None, "adc", "ror", None, # 0x70
	"sei", "adc", None, None, None, "adc", "ror", None, # 0x78
	None, "sta", None, None, "sty", "sta", "stx", None, # 0x80
	"dey", None, "txa", None, "sty", "sta", "stx", None, # 0x88
	"bcc", "sta", None, None, "sty", "sta", "stx", None, # 0x90
	"tya", "sta", "txs", None, None, "sta", None, None, # 0x98
	"ldy", "lda", "ldx", None, "ldy", "lda", "ldx", None, # 0xa0
	"tay", "lda", "tax", None, "ldy", "lda", "ldx", None, # 0xa8
	"bcs", "lda", None, None, "ldy", "lda", "ldx", None, # 0xb0
	"clv", "lda", "tsx", None, "ldy", "lda", "ldx", None, # 0xb8
	"cpy", "cmp", None, None, "cpy", "cmp", "dec", None, # 0xc0
	"iny", "cmp", "dex", None, "cpy", "cmp", "dec", None, # 0xc8
	"bne", "cmp", None, None, None, "cmp", "dec", None, # 0xd0
	"cld", "cmp", None, None, None, "cmp", "dec", None, # 0xd8
	"cpx", "sbc", None, None, "cpx", "sbc", "inc", None, # 0xe0
	"inx", "sbc", "nop", None, "cpx", "sbc", "inc", None, # 0xe8
	"beq", "sbc", None, None, None, "sbc", "inc", None, # 0xf0
	"sed", "sbc", None, None, None, "sbc", "inc", None # 0xf8
]

NONE = 0
ABS = 1
ABS_DEST = 2
ABS_X = 3
ABS_X_DEST = 4
ABS_Y = 5
ABS_Y_DEST = 6
ACCUM = 7
ADDR = 8
IMMED = 9
IND = 10
IND_X = 11
IND_X_DEST = 12
IND_Y = 13
IND_Y_DEST = 14
REL = 15
ZERO = 16
ZERO_DEST = 17
ZERO_X = 18
ZERO_X_DEST = 19
ZERO_Y = 20
ZERO_Y_DEST = 21
InstructionOperandTypes = [
	NONE, IND_X, NONE, NONE, NONE, ZERO, ZERO_DEST, NONE, # 0x00
	NONE, IMMED, ACCUM, NONE, NONE, ABS, ABS_DEST, NONE, # 0x08
	REL, IND_Y, NONE, NONE, NONE, ZERO_X, ZERO_X_DEST, NONE, # 0x10
	NONE, ABS_Y, NONE, NONE, NONE, ABS_X, ABS_X_DEST, NONE, # 0x18
	ADDR, IND_X, NONE, NONE, ZERO, ZERO, ZERO_DEST, NONE, # 0x20
	NONE, IMMED, ACCUM, NONE, ABS, ABS, ABS_DEST, NONE, # 0x28
	REL, IND_Y, NONE, NONE, NONE, ZERO_X, ZERO_X_DEST, NONE, # 0x30
	NONE, ABS_Y, NONE, NONE, NONE, ABS_X, ABS_X_DEST, NONE, # 0x38
	NONE, IND_X, NONE, NONE, NONE, ZERO, ZERO_DEST, NONE, # 0x40
	NONE, IMMED, ACCUM, NONE, ADDR, ABS, ABS_DEST, NONE, # 0x48
	REL, IND_Y, NONE, NONE, NONE, ZERO_X, ZERO_X_DEST, NONE, # 0x50
	NONE, ABS_Y, NONE, NONE, NONE, ABS_X, ABS_X_DEST, NONE, # 0x58
	NONE, IND_X, NONE, NONE, NONE, ZERO, ZERO_DEST, NONE, # 0x60
	NONE, IMMED, ACCUM, NONE, IND, ABS, ABS_DEST, NONE, # 0x68
	REL, IND_Y, NONE, NONE, NONE, ZERO_X, ZERO_X_DEST, NONE, # 0x70
	NONE, ABS_Y, NONE, NONE, NONE, ABS_X, ABS_X_DEST, NONE, # 0x78
	NONE, IND_X_DEST, NONE, NONE, ZERO_DEST, ZERO_DEST, ZERO_DEST, NONE, # 0x80
	NONE, NONE, NONE, NONE, ABS_DEST, ABS_DEST, ABS_DEST, NONE, # 0x88
	REL, IND_Y_DEST, NONE, NONE, ZERO_X_DEST, ZERO_X_DEST, ZERO_Y_DEST, NONE, # 0x90
	NONE, ABS_Y_DEST, NONE, NONE, NONE, ABS_X_DEST, NONE, NONE, # 0x98
	IMMED, IND_X, IMMED, NONE, ZERO, ZERO, ZERO, NONE, # 0xa0
	NONE, IMMED, NONE, NONE, ABS, ABS, ABS, NONE, # 0xa8
	REL, IND_Y, NONE, NONE, ZERO_X, ZERO_X, ZERO_Y, NONE, # 0xb0
	NONE, ABS_Y, NONE, NONE, ABS_X, ABS_X, ABS_Y, NONE, # 0xb8
	IMMED, IND_X, NONE, NONE, ZERO, ZERO, ZERO_DEST, NONE, # 0xc0
	NONE, IMMED, NONE, NONE, ABS, ABS, ABS_DEST, NONE, # 0xc8
	REL, IND_Y, NONE, NONE, NONE, ZERO_X, ZERO_X_DEST, NONE, # 0xd0
	NONE, ABS_Y, NONE, NONE, NONE, ABS_X, ABS_X_DEST, NONE, # 0xd8
	IMMED, IND_X, NONE, NONE, ZERO, ZERO, ZERO_DEST, NONE, # 0xe0
	NONE, IMMED, NONE, NONE, ABS, ABS, ABS_DEST, NONE, # 0xe8
	REL, IND_Y, NONE, NONE, NONE, ZERO_X, ZERO_X_DEST, NONE, # 0xf0
	NONE, ABS_Y, NONE, NONE, NONE, ABS_X, ABS_X_DEST, NONE # 0xf8
]

OperandLengths = [
	0, # NONE
	2, # ABS
	2, # ABS_DEST
	2, # ABS_X
	2, # ABS_X_DEST
	2, # ABS_Y
	2, # ABS_Y_DEST
	0, # ACCUM
	2, # ADDR
	1, # IMMED
	2, # IND
	1, # IND_X
	1, # IND_X_DEST
	1, # IND_Y
	1, # IND_Y_DEST
	1, # REL
	1, # ZERO
	1, # ZREO_DEST
	1, # ZERO_X
	1, # ZERO_X_DEST
	1, # ZERO_Y
	1  # ZERO_Y_DEST
]

OperandTokens = [
	lambda value: [], # NONE
	lambda value: [InstructionTextToken(PossibleAddressToken, "$%.4x" % value, value)], # ABS
	lambda value: [InstructionTextToken(PossibleAddressToken, "$%.4x" % value, value)], # ABS_DEST
	lambda value: [InstructionTextToken(PossibleAddressToken, "$%.4x" % value, value),
		InstructionTextToken(TextToken, ", "), InstructionTextToken(RegisterToken, "x")], # ABS_X
	lambda value: [InstructionTextToken(PossibleAddressToken, "$%.4x" % value, value),
		InstructionTextToken(TextToken, ", "), InstructionTextToken(RegisterToken, "x")], # ABS_X_DEST
	lambda value: [InstructionTextToken(PossibleAddressToken, "$%.4x" % value, value),
		InstructionTextToken(TextToken, ", "), InstructionTextToken(RegisterToken, "y")], # ABS_Y
	lambda value: [InstructionTextToken(PossibleAddressToken, "$%.4x" % value, value),
		InstructionTextToken(TextToken, ", "), InstructionTextToken(RegisterToken, "y")], # ABS_Y_DEST
	lambda value: [InstructionTextToken(RegisterToken, "a")], # ACCUM
	lambda value: [InstructionTextToken(PossibleAddressToken, "$%.4x" % value, value)], # ADDR
	lambda value: [InstructionTextToken(TextToken, "#"), InstructionTextToken(IntegerToken, "$%.2x" % value, value)], # IMMED
	lambda value: [InstructionTextToken(TextToken, "["), InstructionTextToken(PossibleAddressToken, "$%.4x" % value, value),
		InstructionTextToken(TextToken, "]")], # IND
	lambda value: [InstructionTextToken(TextToken, "["), InstructionTextToken(PossibleAddressToken, "$%.2x" % value, value),
		InstructionTextToken(TextToken, ", "), InstructionTextToken(RegisterToken, "x"),
		InstructionTextToken(TextToken, "]")], # IND_X
	lambda value: [InstructionTextToken(TextToken, "["), InstructionTextToken(PossibleAddressToken, "$%.2x" % value, value),
		InstructionTextToken(TextToken, ", "), InstructionTextToken(RegisterToken, "x"),
		InstructionTextToken(TextToken, "]")], # IND_X_DEST
	lambda value: [InstructionTextToken(TextToken, "["), InstructionTextToken(PossibleAddressToken, "$%.2x" % value, value),
		InstructionTextToken(TextToken, "], "), InstructionTextToken(RegisterToken, "y")], # IND_Y
	lambda value: [InstructionTextToken(TextToken, "["), InstructionTextToken(PossibleAddressToken, "$%.2x" % value, value),
		InstructionTextToken(TextToken, "], "), InstructionTextToken(RegisterToken, "y")], # IND_Y_DEST
	lambda value: [InstructionTextToken(PossibleAddressToken, "$%.4x" % value, value)], # REL
	lambda value: [InstructionTextToken(PossibleAddressToken, "$%.2x" % value, value)], # ZERO
	lambda value: [InstructionTextToken(PossibleAddressToken, "$%.2x" % value, value)], # ZERO_DEST
	lambda value: [InstructionTextToken(PossibleAddressToken, "$%.2x" % value, value),
		InstructionTextToken(TextToken, ", "), InstructionTextToken(RegisterToken, "x")], # ZERO_X
	lambda value: [InstructionTextToken(PossibleAddressToken, "$%.2x" % value, value),
		InstructionTextToken(TextToken, ", "), InstructionTextToken(RegisterToken, "x")], # ZERO_X_DEST
	lambda value: [InstructionTextToken(PossibleAddressToken, "$%.2x" % value, value),
		InstructionTextToken(TextToken, ", "), InstructionTextToken(RegisterToken, "y")], # ZERO_Y
	lambda value: [InstructionTextToken(PossibleAddressToken, "$%.2x" % value, value),
		InstructionTextToken(TextToken, ", "), InstructionTextToken(RegisterToken, "y")] # ZERO_Y_DEST
]

def indirect_load(il, value):
	if (value & 0xff) == 0xff:
		lo_addr = il.const(2, value)
		hi_addr = il.const(2, (value & 0xff00) | ((value + 1) & 0xff))
		lo = il.zero_extend(2, il.load(1, lo_addr))
		hi = il.shift_left(2, il.zero_extend(2, il.load(1, hi_addr)), il.const(2, 8))
		return il.or_expr(2, lo, hi)
	return il.load(2, il.const(2, value))

def load_zero_page_16(il, value):
	if il[value].operation == "LLIL_CONST":
		if il[value].value == 0xff:
			lo = il.zero_extend(2, il.load(1, il.const(2, 0xff)))
			hi = il.shift_left(2, il.zero_extend(2, il.load(1, il.const(2, 0)), il.const(2, 8)))
			return il.or_expr(2, lo, hi)
		return il.load(2, il.const(2, il[value].value))
	il.append(il.set_reg(1, LLIL_TEMP(0), value))
	value = il.reg(1, LLIL_TEMP(0))
	lo_addr = value
	hi_addr = il.add(1, value, il.const(1, 1))
	lo = il.zero_extend(2, il.load(1, lo_addr))
	hi = il.shift_left(2, il.zero_extend(2, il.load(1, hi_addr)), il.const(2, 8))
	return il.or_expr(2, lo, hi)

OperandIL = [
	lambda il, value: None, # NONE
	lambda il, value: il.load(1, il.const(2, value)), # ABS
	lambda il, value: il.const(2, value), # ABS_DEST
	lambda il, value: il.load(1, il.add(2, il.const(2, value), il.zero_extend(2, il.reg(1, "x")))), # ABS_X
	lambda il, value: il.add(2, il.const(2, value), il.zero_extend(2, il.reg(1, "x"))), # ABS_X_DEST
	lambda il, value: il.load(1, il.add(2, il.const(2, value), il.zero_extend(2, il.reg(1, "y")))), # ABS_Y
	lambda il, value: il.add(2, il.const(2, value), il.zero_extend(2, il.reg(1, "y"))), # ABS_Y_DEST
	lambda il, value: il.reg(1, "a"), # ACCUM
	lambda il, value: il.const(2, value), # ADDR
	lambda il, value: il.const(1, value), # IMMED
	lambda il, value: indirect_load(il, value), # IND
	lambda il, value: il.load(1, load_zero_page_16(il, il.add(1, il.const(1, value), il.reg(1, "x")))), # IND_X
	lambda il, value: load_zero_page_16(il, il.add(1, il.const(1, value), il.reg(1, "x"))), # IND_X_DEST
	lambda il, value: il.load(1, il.add(2, load_zero_page_16(il, il.const(1, value)), il.reg(1, "y"))), # IND_Y
	lambda il, value: il.add(2, load_zero_page_16(il, il.const(1, value)), il.reg(1, "y")), # IND_Y_DEST
	lambda il, value: il.const(2, value), # REL
	lambda il, value: il.load(1, il.const(2, value)), # ZERO
	lambda il, value: il.const(2, value), # ZERO_DEST
	lambda il, value: il.load(1, il.zero_extend(2, il.add(1, il.const(1, value), il.reg(1, "x")))), # ZERO_X
	lambda il, value: il.zero_extend(2, il.add(1, il.const(1, value), il.reg(1, "x"))), # ZERO_X_DEST
	lambda il, value: il.load(1, il.zero_extend(2, il.add(1, il.const(1, value), il.reg(1, "y")))), # ZERO_Y
	lambda il, value: il.zero_extend(2, il.add(1, il.const(1, value), il.reg(1, "y"))) # ZERO_Y_DEST
]

def cond_branch(il, cond, dest):
	t = None
	if il[dest].operation == LLIL_CONST:
		t = il.get_label_for_address(Architecture['6502'], il[dest].value)
	if t is None:
		t = LowLevelILLabel()
		indirect = True
	else:
		indirect = False
	f = LowLevelILLabel()
	il.append(il.if_expr(cond, t, f))
	if indirect:
		il.mark_label(t)
		il.append(il.jump(dest))
	il.mark_label(f)
	return None

def jump(il, dest):
	label = None
	if il[dest].operation == LLIL_CONST:
		label = il.get_label_for_address(Architecture['6502'], il[dest].value)
	if label is None:
		il.append(il.jump(dest))
	else:
		il.append(il.goto(label))
	return None

def get_p_value(il):
	c = il.flag_bit(1, "c", 0)
	z = il.flag_bit(1, "z", 1)
	i = il.flag_bit(1, "i", 2)
	d = il.flag_bit(1, "d", 3)
	b = il.flag_bit(1, "b", 4)
	v = il.flag_bit(1, "v", 6)
	s = il.flag_bit(1, "s", 7)
	return il.or_expr(1, il.or_expr(1, il.or_expr(1, il.or_expr(1, il.or_expr(1,
	                  il.or_expr(1, c, z), i), d), b), v), s)

def set_p_value(il, value):
	il.append(il.set_reg(1, LLIL_TEMP(0), value))
	il.append(il.set_flag("c", il.test_bit(1, il.reg(1, LLIL_TEMP(0)), il.const(1, 0x01))))
	il.append(il.set_flag("z", il.test_bit(1, il.reg(1, LLIL_TEMP(0)), il.const(1, 0x02))))
	il.append(il.set_flag("i", il.test_bit(1, il.reg(1, LLIL_TEMP(0)), il.const(1, 0x04))))
	il.append(il.set_flag("d", il.test_bit(1, il.reg(1, LLIL_TEMP(0)), il.const(1, 0x08))))
	il.append(il.set_flag("b", il.test_bit(1, il.reg(1, LLIL_TEMP(0)), il.const(1, 0x10))))
	il.append(il.set_flag("v", il.test_bit(1, il.reg(1, LLIL_TEMP(0)), il.const(1, 0x40))))
	il.append(il.set_flag("s", il.test_bit(1, il.reg(1, LLIL_TEMP(0)), il.const(1, 0x80))))
	return None

def rti(il):
	set_p_value(il, il.pop(1))
	return il.ret(il.pop(2))

InstructionIL = {
	"adc": lambda il, operand: il.set_reg(1, "a", il.add_carry(1, il.reg(1, "a"), operand, flags = "*")),
	"asl": lambda il, operand: il.store(1, operand, il.shift_left(1, il.load(1, operand), il.const(1, 1), flags = "czs")),
	"asl@": lambda il, operand: il.set_reg(1, "a", il.shift_left(1, operand, il.const(1, 1), flags = "czs")),
	"and": lambda il, operand: il.set_reg(1, "a", il.and_expr(1, il.reg(1, "a"), operand, flags = "zs")),
	"bcc": lambda il, operand: cond_branch(il, il.flag_condition(LLFC_UGE), operand),
	"bcs": lambda il, operand: cond_branch(il, il.flag_condition(LLFC_ULT), operand),
	"beq": lambda il, operand: cond_branch(il, il.flag_condition(LLFC_E), operand),
	"bit": lambda il, operand: il.and_expr(1, il.reg(1, "a"), operand, flags = "czs"),
	"bmi": lambda il, operand: cond_branch(il, il.flag_condition(LLFC_NEG), operand),
	"bne": lambda il, operand: cond_branch(il, il.flag_condition(LLFC_NE), operand),
	"bpl": lambda il, operand: cond_branch(il, il.flag_condition(LLFC_POS), operand),
	"brk": lambda il, operand: il.system_call(),
	"bvc": lambda il, operand: cond_branch(il, il.not_expr(0, il.flag("v")), operand),
	"bvs": lambda il, operand: cond_branch(il, il.flag("v"), operand),
	"clc": lambda il, operand: il.set_flag("c", il.const(0, 0)),
	"cld": lambda il, operand: il.set_flag("d", il.const(0, 0)),
	"cli": lambda il, operand: il.set_flag("i", il.const(0, 0)),
	"clv": lambda il, operand: il.set_flag("v", il.const(0, 0)),
	"cmp": lambda il, operand: il.sub(1, il.reg(1, "a"), operand, flags = "czs"),
	"cpx": lambda il, operand: il.sub(1, il.reg(1, "x"), operand, flags = "czs"),
	"cpy": lambda il, operand: il.sub(1, il.reg(1, "y"), operand, flags = "czs"),
	"dec": lambda il, operand: il.store(1, operand, il.sub(1, il.load(1, operand), il.const(1, 1), flags = "zs")),
	"dex": lambda il, operand: il.set_reg(1, "x", il.sub(1, il.reg(1, "x"), il.const(1, 1), flags = "zs")),
	"dey": lambda il, operand: il.set_reg(1, "y", il.sub(1, il.reg(1, "y"), il.const(1, 1), flags = "zs")),
	"eor": lambda il, operand: il.set_reg(1, "a", il.xor_expr(1, il.reg(1, "a"), operand, flags = "zs")),
	"inc": lambda il, operand: il.store(1, operand, il.add(1, il.load(1, operand), il.const(1, 1), flags = "zs")),
	"inx": lambda il, operand: il.set_reg(1, "x", il.add(1, il.reg(1, "x"), il.const(1, 1), flags = "zs")),
	"iny": lambda il, operand: il.set_reg(1, "y", il.add(1, il.reg(1, "y"), il.const(1, 1), flags = "zs")),
	"jmp": lambda il, operand: jump(il, operand),
	"jsr": lambda il, operand: il.call(operand),
	"lda": lambda il, operand: il.set_reg(1, "a", operand, flags = "zs"),
	"ldx": lambda il, operand: il.set_reg(1, "x", operand, flags = "zs"),
	"ldy": lambda il, operand: il.set_reg(1, "y", operand, flags = "zs"),
	"lsr": lambda il, operand: il.store(1, operand, il.logical_shift_right(1, il.load(1, operand), il.const(1, 1), flags = "czs")),
	"lsr@": lambda il, operand: il.set_reg(1, "a", il.logical_shift_right(1, il.reg(1, "a"), il.const(1, 1), flags = "czs")),
	"nop": lambda il, operand: il.nop(),
	"ora": lambda il, operand: il.set_reg(1, "a", il.or_expr(1, il.reg(1, "a"), operand, flags = "zs")),
	"pha": lambda il, operand: il.push(1, il.reg(1, "a")),
	"php": lambda il, operand: il.push(1, get_p_value(il)),
	"pla": lambda il, operand: il.set_reg(1, "a", il.pop(1), flags = "zs"),
	"plp": lambda il, operand: set_p_value(il, il.pop(1)),
	"rol": lambda il, operand: il.store(1, operand, il.rotate_left_carry(1, il.load(1, operand), il.const(1, 1), flags = "czs")),
	"rol@": lambda il, operand: il.set_reg(1, "a", il.rotate_left_carry(1, il.reg(1, "a"), il.const(1, 1), flags = "czs")),
	"ror": lambda il, operand: il.store(1, operand, il.rotate_right_carry(1, il.load(1, operand), il.const(1, 1), flags = "czs")),
	"ror@": lambda il, operand: il.set_reg(1, "a", il.rotate_right_carry(1, il.reg(1, "a"), il.const(1, 1), flags = "czs")),
	"rti": lambda il, operand: rti(il),
	"rts": lambda il, operand: il.ret(il.add(2, il.pop(2), il.const(2, 1))),
	"sbc": lambda il, operand: il.set_reg(1, "a", il.sub_borrow(1, il.reg(1, "a"), operand, flags = "*")),
	"sec": lambda il, operand: il.set_flag("c", il.const(0, 1)),
	"sed": lambda il, operand: il.set_flag("d", il.const(0, 1)),
	"sei": lambda il, operand: il.set_flag("i", il.const(0, 1)),
	"sta": lambda il, operand: il.store(1, operand, il.reg(1, "a")),
	"stx": lambda il, operand: il.store(1, operand, il.reg(1, "x")),
	"sty": lambda il, operand: il.store(1, operand, il.reg(1, "y")),
	"tax": lambda il, operand: il.set_reg(1, "x", il.reg(1, "a"), flags = "zs"),
	"tay": lambda il, operand: il.set_reg(1, "y", il.reg(1, "a"), flags = "zs"),
	"tsx": lambda il, operand: il.set_reg(1, "x", il.reg(1, "s"), flags = "zs"),
	"txa": lambda il, operand: il.set_reg(1, "a", il.reg(1, "x"), flags = "zs"),
	"txs": lambda il, operand: il.set_reg(1, "s", il.reg(1, "x")),
	"tya": lambda il, operand: il.set_reg(1, "a", il.reg(1, "y"), flags = "zs")
}

class M6502(Architecture):
	name = "6502"
	address_size = 2
	default_int_size = 1
	regs = {
		"a": RegisterInfo("a", 1),
		"x": RegisterInfo("x", 1),
		"y": RegisterInfo("y", 1),
		"s": RegisterInfo("s", 1)
	}
	stack_pointer = "s"
	flags = ["c", "z", "i", "d", "b", "v", "s"]
	flag_write_types = ["*", "czs", "zvs", "zs"]
	flag_roles = {
		"c": SpecialFlagRole, # Not a normal carry flag, subtract result is inverted
		"z": ZeroFlagRole,
		"v": OverflowFlagRole,
		"s": NegativeSignFlagRole
	}
	flags_required_for_flag_condition = {
		LLFC_UGE: ["c"],
		LLFC_ULT: ["c"],
		LLFC_E: ["z"],
		LLFC_NE: ["z"],
		LLFC_NEG: ["s"],
		LLFC_POS: ["s"]
	}
	flags_written_by_flag_write_type = {
		"*": ["c", "z", "v", "s"],
		"czs": ["c", "z", "s"],
		"zvs": ["z", "v", "s"],
		"zs": ["z", "s"]
	}

	def decode_instruction(self, data, addr):
		if len(data) < 1:
			return None, None, None, None
		opcode = ord(data[0])
		instr = InstructionNames[opcode]
		if instr is None:
			return None, None, None, None

		operand = InstructionOperandTypes[opcode]
		length = 1 + OperandLengths[operand]
		if len(data) < length:
			return None, None, None, None

		if OperandLengths[operand] == 0:
			value = None
		elif operand == REL:
			value = (addr + 2 + struct.unpack("b", data[1])[0]) & 0xffff
		elif OperandLengths[operand] == 1:
			value = ord(data[1])
		else:
			value = struct.unpack("<H", data[1:3])[0]

		return instr, operand, length, value

	def perform_get_instruction_info(self, data, addr):
		instr, operand, length, value = self.decode_instruction(data, addr)
		if instr is None:
			return None

		result = InstructionInfo()
		result.length = length
		if instr == "jmp":
			if operand == ADDR:
				result.add_branch(UnconditionalBranch, struct.unpack("<H", data[1:3])[0])
			else:
				result.add_branch(UnresolvedBranch)
		elif instr == "jsr":
			result.add_branch(CallDestination, struct.unpack("<H", data[1:3])[0])
		elif instr in ["rti", "rts"]:
			result.add_branch(FunctionReturn)
		if instr in ["bcc", "bcs", "beq", "bmi", "bne", "bpl", "bvc", "bvs"]:
			dest = (addr + 2 + struct.unpack("b", data[1])[0]) & 0xffff
			result.add_branch(TrueBranch, dest)
			result.add_branch(FalseBranch, addr + 2)
		return result

	def perform_get_instruction_text(self, data, addr):
		instr, operand, length, value = self.decode_instruction(data, addr)
		if instr is None:
			return None

		tokens = []
		tokens.append(InstructionTextToken(TextToken, "%-7s " % instr.replace("@", "")))
		tokens += OperandTokens[operand](value)
		return tokens, length

	def perform_get_instruction_low_level_il(self, data, addr, il):
		instr, operand, length, value = self.decode_instruction(data, addr)
		if instr is None:
			return None

		operand = OperandIL[operand](il, value)
		instr = InstructionIL[instr](il, operand)
		if isinstance(instr, list):
			for i in instr:
				il.append(i)
		elif instr is not None:
			il.append(instr)

		return length

	def perform_is_never_branch_patch_available(self, data, addr):
		if (data[0] == "\x10") or (data[0] == "\x30") or (data[0] == "\x50") or (data[0] == "\x70") or (data[0] == "\x90") or (data[0] == "\xb0") or (data[0] == "\xd0") or (data[0] == "\xf0"):
			return True
		return False

	def perform_is_invert_branch_patch_available(self, data, addr):
		if (data[0] == "\x10") or (data[0] == "\x30") or (data[0] == "\x50") or (data[0] == "\x70") or (data[0] == "\x90") or (data[0] == "\xb0") or (data[0] == "\xd0") or (data[0] == "\xf0"):
			return True
		return False

	def perform_is_always_branch_patch_available(self, data, addr):
		return False

	def perform_is_skip_and_return_zero_patch_available(self, data, addr):
		return (data[0] == "\x20") and (len(data) == 3)

	def perform_is_skip_and_return_value_patch_available(self, data, addr):
		return (data[0] == "\x20") and (len(data) == 3)

	def perform_convert_to_nop(self, data, addr):
		return "\xea" * len(data)

	def perform_never_branch(self, data, addr):
		if (data[0] == "\x10") or (data[0] == "\x30") or (data[0] == "\x50") or (data[0] == "\x70") or (data[0] == "\x90") or (data[0] == "\xb0") or (data[0] == "\xd0") or (data[0] == "\xf0"):
			return "\xea" * len(data)
		return None

	def perform_invert_branch(self, data, addr):
		if (data[0] == "\x10") or (data[0] == "\x30") or (data[0] == "\x50") or (data[0] == "\x70") or (data[0] == "\x90") or (data[0] == "\xb0") or (data[0] == "\xd0") or (data[0] == "\xf0"):
			return chr(ord(data[0]) ^ 0x20) + data[1:]
		return None

	def perform_skip_and_return_value(self, data, addr, value):
		if (data[0] != "\x20") or (len(data) != 3):
			return None
		return "\xa9" + chr(value & 0xff) + "\xea"

class NESViewUpdateNotification(BinaryDataNotification):
	def __init__(self, view):
		self.view = view

	def data_written(self, view, offset, length):
		addr = offset - self.view.rom_offset
		while length > 0:
			bank_ofs = addr & 0x3fff
			if (bank_ofs + length) > 0x4000:
				to_read = 0x4000 - bank_ofs
			else:
				to_read = length
			if length < to_read:
				to_read = length
			if (addr >= (bank_ofs + (self.view.__class__.bank * 0x4000))) and (addr < (bank_ofs + ((self.view.__class__.bank + 1) * 0x4000))):
				self.view.notify_data_written(0x8000 + bank_ofs, to_read)
			elif (addr >= (bank_ofs + (self.view.rom_length - 0x4000))) and (addr < (bank_ofs + self.view.rom_length)):
				self.view.notify_data_written(0xc000 + bank_ofs, to_read)
			length -= to_read
			addr += to_read

	def data_inserted(self, view, offset, length):
		self.view.notify_data_written(0x8000, 0x8000)

	def data_removed(self, view, offset, length):
		self.view.notify_data_written(0x8000, 0x8000)

class NESView(BinaryView):
	name = "NES"
	long_name = "NES ROM"

	def __init__(self, data):
		BinaryView.__init__(self, data.file)
		self.data = data
		self.notification = NESViewUpdateNotification(self)
		self.data.register_notification(self.notification)

	@classmethod
	def is_valid_for_data(self, data):
		hdr = data.read(0, 16)
		if len(hdr) < 16:
			return False
		if hdr[0:4] != "NES\x1a":
			return False
		rom_banks = struct.unpack("B", hdr[4])[0]
		if rom_banks < (self.bank + 1):
			return False
		return True

	def init(self):
		try:
			hdr = self.data.read(0, 16)
			self.rom_banks = struct.unpack("B", hdr[4])[0]
			self.vrom_banks = struct.unpack("B", hdr[5])[0]
			self.rom_flags = struct.unpack("B", hdr[6])[0]
			self.mapper_index = struct.unpack("B", hdr[7])[0] | (self.rom_flags >> 4)
			self.ram_banks = struct.unpack("B", hdr[8])[0]
			self.rom_offset = 16
			if self.rom_flags & 4:
				self.rom_offset += 512
			self.rom_length = self.rom_banks * 0x4000

			nmi = struct.unpack("<H", self.read(0xfffa, 2))[0]
			start = struct.unpack("<H", self.read(0xfffc, 2))[0]
			irq = struct.unpack("<H", self.read(0xfffe, 2))[0]
			self.define_auto_symbol(Symbol(FunctionSymbol, nmi, "_nmi"))
			self.define_auto_symbol(Symbol(FunctionSymbol, start, "_start"))
			self.define_auto_symbol(Symbol(FunctionSymbol, irq, "_irq"))
			self.add_function(Architecture['6502'].standalone_platform, nmi)
			self.add_function(Architecture['6502'].standalone_platform, irq)
			self.add_entry_point(Architecture['6502'].standalone_platform, start)

			# Hardware registers
			self.define_auto_symbol(Symbol(DataSymbol, 0x2000, "PPUCTRL"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x2001, "PPUMASK"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x2002, "PPUSTATUS"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x2003, "OAMADDR"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x2004, "OAMDATA"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x2005, "PPUSCROLL"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x2006, "PPUADDR"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x2007, "PPUDATA"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x4000, "SQ1_VOL"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x4001, "SQ1_SWEEP"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x4002, "SQ1_LO"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x4003, "SQ1_HI"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x4004, "SQ2_VOL"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x4005, "SQ2_SWEEP"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x4006, "SQ2_LO"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x4007, "SQ2_HI"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x4008, "TRI_LINEAR"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x400a, "TRI_LO"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x400b, "TRI_HI"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x400c, "NOISE_VOL"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x400e, "NOISE_LO"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x400f, "NOISE_HI"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x4010, "DMC_FREQ"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x4011, "DMC_RAW"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x4012, "DMC_START"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x4013, "DMC_LEN"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x4014, "OAMDMA"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x4015, "SND_CHN"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x4016, "JOY1"))
			self.define_auto_symbol(Symbol(DataSymbol, 0x4017, "JOY2"))

			sym_files = [self.data.file.filename + ".%x.nl" % self.__class__.bank,
					self.data.file.filename + ".ram.nl",
					self.data.file.filename + ".%x.nl" % (self.rom_banks - 1)]
			for f in sym_files:
				if os.path.exists(f):
					sym_contents = open(f, "r").read()
					lines = sym_contents.split('\n')
					for line in lines:
						sym = line.split('#')
						if len(sym) < 3:
							break
						addr = int(sym[0][1:], 16)
						name = sym[1]
						self.define_auto_symbol(Symbol(FunctionSymbol, addr, name))
						if addr >= 0x8000:
							self.add_function(Architecture['6502'].standalone_platform, addr)

			return True
		except:
			log_error(traceback.format_exc())
			return False

	def perform_is_valid_offset(self, addr):
		if (addr >= 0x8000) and (addr < 0x10000):
			return True
		return False

	def perform_read(self, addr, length):
		if addr < 0x8000:
			return None
		if addr >= (0x8000 + self.rom_length):
			return None
		if (addr + length) > 0x10000:
			length = 0x10000 - addr
		result = ""
		while length > 0:
			bank_ofs = addr & 0x3fff
			if (bank_ofs + length) > 0x4000:
				to_read = 0x4000 - bank_ofs
			else:
				to_read = length
			if addr < 0xc000:
				data = self.data.read(self.rom_offset + bank_ofs + (self.__class__.bank * 0x4000), to_read)
			else:
				data = self.data.read(self.rom_offset + bank_ofs + self.rom_length - 0x4000, to_read)
			result += data
			if len(data) < to_read:
				break
			length -= to_read
			addr += to_read
		return result

	def perform_write(self, addr, value):
		if addr < 0x8000:
			return 0
		if addr >= (0x8000 + self.rom_length):
			return 0
		if (addr + len(value)) > (0x8000 + self.rom_length):
			length = (0x8000 + self.rom_length) - addr
		else:
			length = len(value)
		if (addr + length) > 0x10000:
			length = 0x10000 - addr
		offset = 0
		while length > 0:
			bank_ofs = addr & 0x3fff
			if (bank_ofs + length) > 0x4000:
				to_write = 0x4000 - bank_ofs
			else:
				to_write = length
			if addr < 0xc000:
				written = self.data.write(self.rom_offset + bank_ofs + (self.__class__.bank * 0x4000), value[offset : offset + to_write])
			else:
				written = self.data.write(self.rom_offset + bank_ofs + self.rom_length - 0x4000, value[offset : offset + to_write])
			if written < to_write:
				break
			length -= to_write
			addr += to_write
			offset += to_write
		return offset

	def perform_get_start(self):
		return 0

	def perform_get_length(self):
		return 0x10000

	def perform_is_executable(self):
		return True

	def perform_get_entry_point(self):
		return struct.unpack("<H", str(self.perform_read(0xfffc, 2)))[0]

banks = []
for i in xrange(0, 32):
	class NESViewBank(NESView):
		bank = i
		name = "NES Bank %X" % i
		long_name = "NES ROM (bank %X)" % i

		def __init__(self, data):
			NESView.__init__(self, data)

	banks.append(NESViewBank)
	NESViewBank.register()

M6502.register()
