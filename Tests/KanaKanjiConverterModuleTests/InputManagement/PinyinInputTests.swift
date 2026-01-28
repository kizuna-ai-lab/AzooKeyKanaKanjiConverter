//
//  PinyinInputTests.swift
//  KanaKanjiConverterModuleTests
//
//  Tests for hybrid romaji + pinyin input functionality.
//

@testable import KanaKanjiConverterModule
import XCTest

final class PinyinInputTests: XCTestCase {

    // MARK: - Helper Methods

    private var dictionaryMockURL: URL {
        Bundle.module.resourceURL!.appendingPathComponent("DictionaryMock", isDirectory: true)
    }

    func sequentialInput(_ composingText: inout ComposingText, sequence: String, inputStyle: InputStyle) {
        for char in sequence {
            composingText.insertAtCursorPosition(String(char), inputStyle: inputStyle)
        }
    }

    // MARK: - rawRomanInput Tests

    func testRawRomanInputWithRomaji() throws {
        var c = ComposingText()
        sequentialInput(&c, sequence: "watashi", inputStyle: .roman2kana)

        // convertTarget should be kana
        XCTAssertEqual(c.convertTarget, "わたし")

        // rawRomanInput should preserve original roman characters
        XCTAssertEqual(c.rawRomanInput, "watashi")
    }

    func testRawRomanInputWithMixedInput() throws {
        var c = ComposingText()
        sequentialInput(&c, sequence: "nihongo", inputStyle: .roman2kana)

        XCTAssertEqual(c.convertTarget, "にほんご")
        XCTAssertEqual(c.rawRomanInput, "nihongo")
    }

    func testRawRomanInputSubstring() throws {
        var c = ComposingText()
        sequentialInput(&c, sequence: "watashino", inputStyle: .roman2kana)

        // Test substring extraction from specific position
        let substring1 = c.rawRomanInput(from: 0, maxLength: 7)
        XCTAssertEqual(substring1, "watashi")

        let substring2 = c.rawRomanInput(from: 7, maxLength: 2)
        XCTAssertEqual(substring2, "no")

        // Test with longer maxLength than available
        let substring3 = c.rawRomanInput(from: 5, maxLength: 100)
        XCTAssertEqual(substring3, "hino")
    }

    func testRawRomanInputEmptyComposingText() throws {
        let c = ComposingText()

        XCTAssertEqual(c.rawRomanInput, "")
        XCTAssertEqual(c.rawRomanInput(from: 0, maxLength: 10), "")
    }

    func testRawRomanInputWithSpecialCharacters() throws {
        var c = ComposingText()
        sequentialInput(&c, sequence: "xian", inputStyle: .roman2kana)

        // xian converts to kana differently, but rawRomanInput preserves original
        XCTAssertEqual(c.rawRomanInput, "xian")
    }

    func testRawRomanInputLowercaseConversion() throws {
        var c = ComposingText()
        // Note: roman2kana typically works with lowercase, but test the behavior
        sequentialInput(&c, sequence: "nihon", inputStyle: .roman2kana)

        // rawRomanInput(from:maxLength:) should return lowercase
        let result = c.rawRomanInput(from: 0, maxLength: 5)
        XCTAssertEqual(result, "nihon")
    }

    func testRawRomanInputBoundaryConditions() throws {
        var c = ComposingText()
        sequentialInput(&c, sequence: "abc", inputStyle: .roman2kana)

        // Start index at end
        let result1 = c.rawRomanInput(from: 3, maxLength: 5)
        XCTAssertEqual(result1, "")

        // Start index beyond end
        let result2 = c.rawRomanInput(from: 10, maxLength: 5)
        XCTAssertEqual(result2, "")

        // Zero maxLength
        let result3 = c.rawRomanInput(from: 0, maxLength: 0)
        XCTAssertEqual(result3, "")
    }

    // MARK: - Pinyin State Tests

    func testPinyinLookupDisabledByDefault() throws {
        let store = DicdataStore(dictionaryURL: dictionaryMockURL)
        let state = store.prepareState()
        XCTAssertFalse(state.enablePinyinLookup)
    }

    func testPinyinLookupToggle() throws {
        let store = DicdataStore(dictionaryURL: dictionaryMockURL)
        let state = store.prepareState()

        state.updatePinyinLookupEnabled(true)
        XCTAssertTrue(state.enablePinyinLookup)

        state.updatePinyinLookupEnabled(false)
        XCTAssertFalse(state.enablePinyinLookup)
    }

    func testPinyinDictionaryNotLoadedInitially() throws {
        let store = DicdataStore(dictionaryURL: dictionaryMockURL)
        let state = store.prepareState()
        XCTAssertFalse(state.pinyinDictionaryHasLoaded)
        XCTAssertNil(state.pinyinDictionaryLOUDS)
    }

    func testPinyinDictionaryStateUpdate() throws {
        let store = DicdataStore(dictionaryURL: dictionaryMockURL)
        let state = store.prepareState()

        // Simulate loading pinyin dictionary (with nil to indicate not available)
        let nilLouds: LOUDS? = nil
        state.updatePinyinDictionaryLOUDS(nilLouds)
        XCTAssertTrue(state.pinyinDictionaryHasLoaded)
        XCTAssertNil(state.pinyinDictionaryLOUDS)
    }

    // MARK: - Pinyin Search Tests (without dictionary)

    func testPinyinSearchReturnsEmptyWhenDisabled() throws {
        let store = DicdataStore(dictionaryURL: dictionaryMockURL)
        let state = store.prepareState()

        // Pinyin lookup is disabled by default
        XCTAssertFalse(state.enablePinyinLookup)

        // Search should return empty when disabled
        let results = store.pinyinSearchWithLength(
            romanInput: "zhongguo",
            startIndex: 0,
            maxLength: 20,
            state: state
        )
        XCTAssertTrue(results.isEmpty)
    }

    func testPinyinSearchReturnsEmptyWhenNoDictionary() throws {
        let store = DicdataStore(dictionaryURL: dictionaryMockURL)
        let state = store.prepareState()

        // Enable pinyin lookup
        state.updatePinyinLookupEnabled(true)

        // Search should return empty when no pinyin dictionary exists
        // (DictionaryMock doesn't have pinyin.louds)
        let results = store.pinyinSearchWithLength(
            romanInput: "zhongguo",
            startIndex: 0,
            maxLength: 20,
            state: state
        )
        XCTAssertTrue(results.isEmpty)
    }
}
