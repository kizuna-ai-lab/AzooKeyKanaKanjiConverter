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

    /// Create a temporary pinyin dictionary for testing
    /// Returns the URL of the temporary directory containing the pinyin dictionary
    private func createPinyinTestDictionary() throws -> URL {
        let tempDir = FileManager.default.temporaryDirectory.appendingPathComponent("PinyinTestDict-\(UUID().uuidString)", isDirectory: true)
        let loudsDir = tempDir.appendingPathComponent("louds", isDirectory: true)
        try FileManager.default.createDirectory(at: loudsDir, withIntermediateDirectories: true)

        // Copy charID.chid from DictionaryMock
        let sourceCharID = dictionaryMockURL.appendingPathComponent("louds/charID.chid", isDirectory: false)
        let destCharID = loudsDir.appendingPathComponent("charID.chid", isDirectory: false)
        try FileManager.default.copyItem(at: sourceCharID, to: destCharID)

        // Load character mapping
        let charIDString = try String(contentsOf: sourceCharID, encoding: .utf8)
        let char2UInt8 = Dictionary(uniqueKeysWithValues: charIDString.enumerated().map { ($0.element, UInt8($0.offset)) })

        // Create test pinyin entries
        // ruby = pinyin (lowercase), word = Chinese characters
        let pinyinEntries: [DicdataElement] = [
            DicdataElement(word: "中", ruby: "zhong", cid: 1, mid: 1, value: -5),
            DicdataElement(word: "中国", ruby: "zhongguo", cid: 1, mid: 1, value: -3),
            DicdataElement(word: "中文", ruby: "zhongwen", cid: 1, mid: 1, value: -4),
            DicdataElement(word: "国", ruby: "guo", cid: 1, mid: 1, value: -5),
            DicdataElement(word: "国家", ruby: "guojia", cid: 1, mid: 1, value: -4),
            DicdataElement(word: "你", ruby: "ni", cid: 1, mid: 1, value: -5),
            DicdataElement(word: "好", ruby: "hao", cid: 1, mid: 1, value: -5),
            DicdataElement(word: "我", ruby: "wo", cid: 1, mid: 1, value: -5),
            DicdataElement(word: "是", ruby: "shi", cid: 1, mid: 1, value: -5),
            DicdataElement(word: "日本", ruby: "riben", cid: 1, mid: 1, value: -4),
            // 同音词测试 (homophone test)
            DicdataElement(word: "人参", ruby: "renshen", cid: 1, mid: 1, value: -4),
            DicdataElement(word: "人身", ruby: "renshen", cid: 1, mid: 1, value: -4),
            DicdataElement(word: "人", ruby: "ren", cid: 1, mid: 1, value: -5),
        ]

        // Export pinyin dictionary using DictionaryBuilder
        // Use baseName "pinyin" and shardByFirstCharacter=false to create pinyin.louds, pinyin.loudschars2, pinyin0.loudstxt3
        try DictionaryBuilder.exportDictionary(
            entries: pinyinEntries,
            to: loudsDir,
            baseName: "pinyin",
            shardByFirstCharacter: false,
            char2UInt8: char2UInt8
        )

        return tempDir
    }

    /// Clean up temporary directory
    private func cleanupTempDirectory(_ url: URL) {
        try? FileManager.default.removeItem(at: url)
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

    // MARK: - Key InputPiece Tests (Desktop App Simulation)

    /// Test rawRomanInput with .key InputPiece type
    /// This simulates how azooKey-Desktop creates input through getUserAction/keyMap
    /// The Desktop app uses .key type for Japanese input mode (including roman2kana)
    func testRawRomanInputWithKeyInputPiece() throws {
        var c = ComposingText()

        // Simulate Desktop app input: creates .key InputPiece for Japanese input
        // This is how UserAction.keyMap creates input for inputLanguage == .japanese
        let elements = "nihao".map { char in
            ComposingText.InputElement(
                piece: .key(intention: nil, input: char, modifiers: []),
                inputStyle: .roman2kana
            )
        }
        c.insertAtCursorPosition(elements)

        // rawRomanInput should extract characters from .key InputPiece
        XCTAssertEqual(c.rawRomanInput, "nihao")
    }

    /// Test rawRomanInput(from:maxLength:) with .key InputPiece type
    func testRawRomanInputSubstringWithKeyInputPiece() throws {
        var c = ComposingText()

        // Simulate Desktop app input with pinyin
        let elements = "zhongguo".map { char in
            ComposingText.InputElement(
                piece: .key(intention: nil, input: char, modifiers: []),
                inputStyle: .roman2kana
            )
        }
        c.insertAtCursorPosition(elements)

        // Test substring extraction
        let substring1 = c.rawRomanInput(from: 0, maxLength: 5)
        XCTAssertEqual(substring1, "zhong")

        let substring2 = c.rawRomanInput(from: 5, maxLength: 3)
        XCTAssertEqual(substring2, "guo")

        // Full string
        XCTAssertEqual(c.rawRomanInput, "zhongguo")
    }

    /// Test mixed InputPiece types (both .character and .key)
    func testRawRomanInputWithMixedInputPieceTypes() throws {
        var c = ComposingText()

        // First insert some .character type (like English input)
        c.insertAtCursorPosition("ab", inputStyle: .roman2kana)

        // Then insert .key type (like Japanese input)
        let keyElements = "cd".map { char in
            ComposingText.InputElement(
                piece: .key(intention: nil, input: char, modifiers: []),
                inputStyle: .roman2kana
            )
        }
        c.insertAtCursorPosition(keyElements)

        // rawRomanInput should handle both types
        XCTAssertEqual(c.rawRomanInput, "abcd")
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

    // MARK: - Pinyin Search Tests (with dictionary) - Integration Tests

    /// Test that pinyin search returns results when dictionary is available
    /// This is the critical test that was missing - it validates the complete search path
    func testPinyinSearchReturnsResultsWithDictionary() throws {
        let pinyinDictURL = try createPinyinTestDictionary()
        defer { cleanupTempDirectory(pinyinDictURL) }

        let store = DicdataStore(dictionaryURL: dictionaryMockURL)
        let state = store.prepareState()

        // Enable pinyin lookup and set pinyin dictionary URL
        state.updatePinyinLookupEnabled(true)
        state.updatePinyinDictionaryURL(pinyinDictURL)

        // Search for "zhongguo" - should find "中国"
        let results = store.pinyinSearchWithLength(
            romanInput: "zhongguo",
            startIndex: 0,
            maxLength: 20,
            state: state
        )

        // This is the key assertion that was missing before
        XCTAssertFalse(results.isEmpty, "Pinyin search should return results when dictionary is available")

        // Verify we found the expected entry
        let zhongguoResults = results.filter { $0.element.word == "中国" }
        XCTAssertFalse(zhongguoResults.isEmpty, "Should find '中国' for pinyin 'zhongguo'")

        // Verify the pinyin length is correct
        if let match = zhongguoResults.first {
            XCTAssertEqual(match.pinyinLength, 8, "Pinyin length for 'zhongguo' should be 8")
            XCTAssertEqual(match.element.ruby.lowercased(), "zhongguo")
        }
    }

    /// Test that pinyin search finds partial matches at different lengths
    func testPinyinSearchFindsPartialMatches() throws {
        let pinyinDictURL = try createPinyinTestDictionary()
        defer { cleanupTempDirectory(pinyinDictURL) }

        let store = DicdataStore(dictionaryURL: dictionaryMockURL)
        let state = store.prepareState()

        state.updatePinyinLookupEnabled(true)
        state.updatePinyinDictionaryURL(pinyinDictURL)

        // Search for "zhongwen" - should find both "中" (zhong) and "中文" (zhongwen)
        let results = store.pinyinSearchWithLength(
            romanInput: "zhongwen",
            startIndex: 0,
            maxLength: 20,
            state: state
        )

        XCTAssertFalse(results.isEmpty, "Should find results for 'zhongwen'")

        // Should find "中" with length 5
        let zhongResults = results.filter { $0.element.word == "中" && $0.pinyinLength == 5 }
        XCTAssertFalse(zhongResults.isEmpty, "Should find '中' with pinyin length 5")

        // Should find "中文" with length 8
        let zhongwenResults = results.filter { $0.element.word == "中文" && $0.pinyinLength == 8 }
        XCTAssertFalse(zhongwenResults.isEmpty, "Should find '中文' with pinyin length 8")
    }

    /// Test pinyin search with startIndex offset
    func testPinyinSearchWithStartIndex() throws {
        let pinyinDictURL = try createPinyinTestDictionary()
        defer { cleanupTempDirectory(pinyinDictURL) }

        let store = DicdataStore(dictionaryURL: dictionaryMockURL)
        let state = store.prepareState()

        state.updatePinyinLookupEnabled(true)
        state.updatePinyinDictionaryURL(pinyinDictURL)

        // Input is "wozhongguo", search starting from index 2 should find "zhongguo"
        let results = store.pinyinSearchWithLength(
            romanInput: "wozhongguo",
            startIndex: 2,
            maxLength: 20,
            state: state
        )

        XCTAssertFalse(results.isEmpty, "Should find results starting from index 2")

        let zhongguoResults = results.filter { $0.element.word == "中国" }
        XCTAssertFalse(zhongguoResults.isEmpty, "Should find '中国' when searching from index 2")
    }

    /// Test that single character pinyin matches work
    func testPinyinSearchSingleCharacter() throws {
        let pinyinDictURL = try createPinyinTestDictionary()
        defer { cleanupTempDirectory(pinyinDictURL) }

        let store = DicdataStore(dictionaryURL: dictionaryMockURL)
        let state = store.prepareState()

        state.updatePinyinLookupEnabled(true)
        state.updatePinyinDictionaryURL(pinyinDictURL)

        // Search for "ni" - should find "你"
        let results = store.pinyinSearchWithLength(
            romanInput: "ni",
            startIndex: 0,
            maxLength: 20,
            state: state
        )

        XCTAssertFalse(results.isEmpty, "Should find results for 'ni'")

        let niResults = results.filter { $0.element.word == "你" }
        XCTAssertFalse(niResults.isEmpty, "Should find '你' for pinyin 'ni'")
    }

    /// Test that escapedIdentifier correctly handles "pinyin" identifier
    /// This test specifically validates the bug fix for the escapedIdentifier function
    func testEscapedIdentifierForPinyin() throws {
        // "pinyin" should be returned as-is, not escaped to hex format
        let escaped = DictionaryBuilder.escapedIdentifier("pinyin")
        XCTAssertEqual(escaped, "pinyin", "escapedIdentifier should return 'pinyin' as-is, not escape it to hex")

        // Verify other special cases still work
        XCTAssertEqual(DictionaryBuilder.escapedIdentifier("user"), "user")
        XCTAssertEqual(DictionaryBuilder.escapedIdentifier("memory"), "memory")
        XCTAssertEqual(DictionaryBuilder.escapedIdentifier("user_shortcuts"), "user_shortcuts")

        // Verify non-special identifiers are still escaped
        let escapedOther = DictionaryBuilder.escapedIdentifier("test")
        XCTAssertNotEqual(escapedOther, "test", "Non-special identifiers should be escaped")
        XCTAssertTrue(escapedOther.hasPrefix("["), "Escaped identifier should start with '['")
    }

    /// Test that pinyin search returns multiple homophones (同音词)
    /// For "renshen", should find both "人参" and "人身"
    func testPinyinSearchReturnsHomophones() throws {
        let pinyinDictURL = try createPinyinTestDictionary()
        defer { cleanupTempDirectory(pinyinDictURL) }

        let store = DicdataStore(dictionaryURL: dictionaryMockURL)
        let state = store.prepareState()

        state.updatePinyinLookupEnabled(true)
        state.updatePinyinDictionaryURL(pinyinDictURL)

        // Search for "renshen" - should find both "人参" and "人身"
        let results = store.pinyinSearchWithLength(
            romanInput: "renshen",
            startIndex: 0,
            maxLength: 20,
            state: state
        )

        XCTAssertFalse(results.isEmpty, "Should find results for 'renshen'")

        // Extract all words found for "renshen"
        let renshenWords = results
            .filter { $0.pinyinLength == 7 }  // "renshen" has 7 characters
            .map { $0.element.word }

        // Should find "人参"
        XCTAssertTrue(renshenWords.contains("人参"), "Should find '人参' for pinyin 'renshen'")

        // Should find "人身"
        XCTAssertTrue(renshenWords.contains("人身"), "Should find '人身' for pinyin 'renshen'")

        // Should have at least 2 results for the full pinyin
        XCTAssertGreaterThanOrEqual(renshenWords.count, 2, "Should find at least 2 homophones for 'renshen'")

        // Should also find partial match "人" for "ren"
        let renResults = results.filter { $0.element.word == "人" && $0.pinyinLength == 3 }
        XCTAssertFalse(renResults.isEmpty, "Should find '人' for partial pinyin 'ren'")
    }
}
