import { UnknownFieldHandler } from "@protobuf-ts/runtime";
import { WireType } from "@protobuf-ts/runtime";
import { reflectionMergePartial } from "@protobuf-ts/runtime";
import { MessageType } from "@protobuf-ts/runtime";
// @generated message type with reflection information, may provide speed optimized methods
class TileSet$Type extends MessageType {
    constructor() {
        super("wpmaps.TileSet", [
            { no: 1, name: "deltas", kind: "scalar", repeat: 1 /*RepeatType.PACKED*/, T: 13 /*ScalarType.UINT32*/ }
        ]);
    }
    create(value) {
        const message = globalThis.Object.create((this.messagePrototype));
        message.deltas = [];
        if (value !== undefined)
            reflectionMergePartial(this, message, value);
        return message;
    }
    internalBinaryRead(reader, length, options, target) {
        let message = target ?? this.create(), end = reader.pos + length;
        while (reader.pos < end) {
            let [fieldNo, wireType] = reader.tag();
            switch (fieldNo) {
                case /* repeated uint32 deltas */ 1:
                    if (wireType === WireType.LengthDelimited)
                        for (let e = reader.int32() + reader.pos; reader.pos < e;)
                            message.deltas.push(reader.uint32());
                    else
                        message.deltas.push(reader.uint32());
                    break;
                default:
                    let u = options.readUnknownField;
                    if (u === "throw")
                        throw new globalThis.Error(`Unknown field ${fieldNo} (wire type ${wireType}) for ${this.typeName}`);
                    let d = reader.skip(wireType);
                    if (u !== false)
                        (u === true ? UnknownFieldHandler.onRead : u)(this.typeName, message, fieldNo, wireType, d);
            }
        }
        return message;
    }
    internalBinaryWrite(message, writer, options) {
        /* repeated uint32 deltas = 1; */
        if (message.deltas.length) {
            writer.tag(1, WireType.LengthDelimited).fork();
            for (let i = 0; i < message.deltas.length; i++)
                writer.uint32(message.deltas[i]);
            writer.join();
        }
        let u = options.writeUnknownFields;
        if (u !== false)
            (u == true ? UnknownFieldHandler.onWrite : u)(this.typeName, message, writer);
        return writer;
    }
}
/**
 * @generated MessageType for protobuf message wpmaps.TileSet
 */
export const TileSet = new TileSet$Type();
// @generated message type with reflection information, may provide speed optimized methods
class TileSetList$Type extends MessageType {
    constructor() {
        super("wpmaps.TileSetList", [
            { no: 1, name: "tilesets", kind: "message", repeat: 2 /*RepeatType.UNPACKED*/, T: () => TileSet }
        ]);
    }
    create(value) {
        const message = globalThis.Object.create((this.messagePrototype));
        message.tilesets = [];
        if (value !== undefined)
            reflectionMergePartial(this, message, value);
        return message;
    }
    internalBinaryRead(reader, length, options, target) {
        let message = target ?? this.create(), end = reader.pos + length;
        while (reader.pos < end) {
            let [fieldNo, wireType] = reader.tag();
            switch (fieldNo) {
                case /* repeated wpmaps.TileSet tilesets */ 1:
                    message.tilesets.push(TileSet.internalBinaryRead(reader, reader.uint32(), options));
                    break;
                default:
                    let u = options.readUnknownField;
                    if (u === "throw")
                        throw new globalThis.Error(`Unknown field ${fieldNo} (wire type ${wireType}) for ${this.typeName}`);
                    let d = reader.skip(wireType);
                    if (u !== false)
                        (u === true ? UnknownFieldHandler.onRead : u)(this.typeName, message, fieldNo, wireType, d);
            }
        }
        return message;
    }
    internalBinaryWrite(message, writer, options) {
        /* repeated wpmaps.TileSet tilesets = 1; */
        for (let i = 0; i < message.tilesets.length; i++)
            TileSet.internalBinaryWrite(message.tilesets[i], writer.tag(1, WireType.LengthDelimited).fork(), options).join();
        let u = options.writeUnknownFields;
        if (u !== false)
            (u == true ? UnknownFieldHandler.onWrite : u)(this.typeName, message, writer);
        return writer;
    }
}
/**
 * @generated MessageType for protobuf message wpmaps.TileSetList
 */
export const TileSetList = new TileSetList$Type();
// @generated message type with reflection information, may provide speed optimized methods
class WikiGeoData$Type extends MessageType {
    constructor() {
        super("wpmaps.WikiGeoData", [
            { no: 1, name: "q_id", kind: "scalar", T: 13 /*ScalarType.UINT32*/ },
            { no: 2, name: "name", kind: "scalar", T: 9 /*ScalarType.STRING*/ },
            { no: 3, name: "longitude", kind: "scalar", T: 17 /*ScalarType.SINT32*/ },
            { no: 4, name: "latitude", kind: "scalar", T: 17 /*ScalarType.SINT32*/ },
            { no: 5, name: "logrank", kind: "scalar", T: 13 /*ScalarType.UINT32*/ }
        ]);
    }
    create(value) {
        const message = globalThis.Object.create((this.messagePrototype));
        message.qId = 0;
        message.name = "";
        message.longitude = 0;
        message.latitude = 0;
        message.logrank = 0;
        if (value !== undefined)
            reflectionMergePartial(this, message, value);
        return message;
    }
    internalBinaryRead(reader, length, options, target) {
        let message = target ?? this.create(), end = reader.pos + length;
        while (reader.pos < end) {
            let [fieldNo, wireType] = reader.tag();
            switch (fieldNo) {
                case /* uint32 q_id */ 1:
                    message.qId = reader.uint32();
                    break;
                case /* string name */ 2:
                    message.name = reader.string();
                    break;
                case /* sint32 longitude */ 3:
                    message.longitude = reader.sint32();
                    break;
                case /* sint32 latitude */ 4:
                    message.latitude = reader.sint32();
                    break;
                case /* uint32 logrank */ 5:
                    message.logrank = reader.uint32();
                    break;
                default:
                    let u = options.readUnknownField;
                    if (u === "throw")
                        throw new globalThis.Error(`Unknown field ${fieldNo} (wire type ${wireType}) for ${this.typeName}`);
                    let d = reader.skip(wireType);
                    if (u !== false)
                        (u === true ? UnknownFieldHandler.onRead : u)(this.typeName, message, fieldNo, wireType, d);
            }
        }
        return message;
    }
    internalBinaryWrite(message, writer, options) {
        /* uint32 q_id = 1; */
        if (message.qId !== 0)
            writer.tag(1, WireType.Varint).uint32(message.qId);
        /* string name = 2; */
        if (message.name !== "")
            writer.tag(2, WireType.LengthDelimited).string(message.name);
        /* sint32 longitude = 3; */
        if (message.longitude !== 0)
            writer.tag(3, WireType.Varint).sint32(message.longitude);
        /* sint32 latitude = 4; */
        if (message.latitude !== 0)
            writer.tag(4, WireType.Varint).sint32(message.latitude);
        /* uint32 logrank = 5; */
        if (message.logrank !== 0)
            writer.tag(5, WireType.Varint).uint32(message.logrank);
        let u = options.writeUnknownFields;
        if (u !== false)
            (u == true ? UnknownFieldHandler.onWrite : u)(this.typeName, message, writer);
        return writer;
    }
}
/**
 * @generated MessageType for protobuf message wpmaps.WikiGeoData
 */
export const WikiGeoData = new WikiGeoData$Type();
// @generated message type with reflection information, may provide speed optimized methods
class WikiGeoDataList$Type extends MessageType {
    constructor() {
        super("wpmaps.WikiGeoDataList", [
            { no: 1, name: "items", kind: "message", repeat: 2 /*RepeatType.UNPACKED*/, T: () => WikiGeoData }
        ]);
    }
    create(value) {
        const message = globalThis.Object.create((this.messagePrototype));
        message.items = [];
        if (value !== undefined)
            reflectionMergePartial(this, message, value);
        return message;
    }
    internalBinaryRead(reader, length, options, target) {
        let message = target ?? this.create(), end = reader.pos + length;
        while (reader.pos < end) {
            let [fieldNo, wireType] = reader.tag();
            switch (fieldNo) {
                case /* repeated wpmaps.WikiGeoData items */ 1:
                    message.items.push(WikiGeoData.internalBinaryRead(reader, reader.uint32(), options));
                    break;
                default:
                    let u = options.readUnknownField;
                    if (u === "throw")
                        throw new globalThis.Error(`Unknown field ${fieldNo} (wire type ${wireType}) for ${this.typeName}`);
                    let d = reader.skip(wireType);
                    if (u !== false)
                        (u === true ? UnknownFieldHandler.onRead : u)(this.typeName, message, fieldNo, wireType, d);
            }
        }
        return message;
    }
    internalBinaryWrite(message, writer, options) {
        /* repeated wpmaps.WikiGeoData items = 1; */
        for (let i = 0; i < message.items.length; i++)
            WikiGeoData.internalBinaryWrite(message.items[i], writer.tag(1, WireType.LengthDelimited).fork(), options).join();
        let u = options.writeUnknownFields;
        if (u !== false)
            (u == true ? UnknownFieldHandler.onWrite : u)(this.typeName, message, writer);
        return writer;
    }
}
/**
 * @generated MessageType for protobuf message wpmaps.WikiGeoDataList
 */
export const WikiGeoDataList = new WikiGeoDataList$Type();
