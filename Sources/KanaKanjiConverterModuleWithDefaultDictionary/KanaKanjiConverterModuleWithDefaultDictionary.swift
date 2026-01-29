public import Foundation
@_exported public import KanaKanjiConverterModule

/// Default dictionary URL for the main dictionary
public func defaultDictionaryURL() -> URL {
    #if os(iOS) || os(watchOS) || os(tvOS) || os(visionOS)
    return Bundle.module.bundleURL.appendingPathComponent("Dictionary", isDirectory: true)
    #elseif os(macOS)
    return Bundle.module.resourceURL!.appendingPathComponent("Dictionary", isDirectory: true)
    #else
    return Bundle.module.resourceURL!.appendingPathComponent("Dictionary", isDirectory: true)
    #endif
}

/// Default dictionary URL for the pinyin dictionary (separate from main dictionary)
public func defaultPinyinDictionaryURL() -> URL {
    #if os(iOS) || os(watchOS) || os(tvOS) || os(visionOS)
    return Bundle.module.bundleURL.appendingPathComponent("PinyinDictionary", isDirectory: true)
    #elseif os(macOS)
    return Bundle.module.resourceURL!.appendingPathComponent("PinyinDictionary", isDirectory: true)
    #else
    return Bundle.module.resourceURL!.appendingPathComponent("PinyinDictionary", isDirectory: true)
    #endif
}

public extension DicdataStore {
    static func withDefaultDictionary(preloadDictionary: Bool = false) -> Self {
        let dictionaryDirectory = defaultDictionaryURL()
        return .init(dictionaryURL: dictionaryDirectory, preloadDictionary: preloadDictionary)
    }
}

public extension KanaKanjiConverter {
    static func withDefaultDictionary(preloadDictionary: Bool = false) -> Self {
        let converter = Self.init(dicdataStore: .withDefaultDictionary(preloadDictionary: preloadDictionary))
        // Set the pinyin dictionary URL to the separate PinyinDictionary folder
        let pinyinURL = defaultPinyinDictionaryURL()
        converter.setPinyinDictionaryURL(pinyinURL)
        return converter
    }
}

public extension TextReplacer {
    static func withDefaultEmojiDictionary() -> Self {
        self.init {
            let directoryName = "EmojiDictionary"
            #if os(iOS) || os(watchOS) || os(tvOS) || os(visionOS)
            let directory = Bundle.module.bundleURL.appendingPathComponent(directoryName, isDirectory: true)
            return if #available(iOS 18.4, *) {
                directory.appendingPathComponent("emoji_all_E16.0.txt", isDirectory: false)
            } else if #available(iOS 17.4, *) {
                directory.appendingPathComponent("emoji_all_E15.1.txt", isDirectory: false)
            } else if #available(iOS 16.4, *) {
                directory.appendingPathComponent("emoji_all_E15.0.txt", isDirectory: false)
            } else if #available(iOS 15.4, *) {
                directory.appendingPathComponent("emoji_all_E14.0.txt", isDirectory: false)
            } else {
                directory.appendingPathComponent("emoji_all_E13.1.txt", isDirectory: false)
            }
            #elseif os(macOS)
            let directory = Bundle.module.resourceURL!.appendingPathComponent(directoryName, isDirectory: true)
            return if #available(macOS 15.3, *) {
                directory.appendingPathComponent("emoji_all_E16.0.txt", isDirectory: false)
            } else if #available(macOS 14.4, *) {
                directory.appendingPathComponent("emoji_all_E15.1.txt", isDirectory: false)
            } else {
                directory.appendingPathComponent("emoji_all_E15.0.txt", isDirectory: false)
            }
            #else
            return Bundle.module.resourceURL!
                .appendingPathComponent(directoryName, isDirectory: true)
                .appendingPathComponent("emoji_all_E16.0.txt", isDirectory: false)
            #endif
        }
    }
}
