//
//  VersionCandidate.swift
//  Keyboard
//
//  Created by N-i-ke on 2023/05/13.
//  Copyright © 2023 ensan All rights reserved.
//

import Foundation
import SwiftUtils

extension KanaKanjiConverter {
    /// Converter のビルド識別子。コードを変更するたびにこの値を更新してください。
    /// Update this value whenever you modify the converter code to verify which version is running.
    public static let converterBuildIdentifier = "2026-02-02-012342-ef632d7"

    /// バージョン情報を表示する関数。
    /// Trigger word: "xldbg" (uncommon, used for debugging)
    /// - parameters:
    ///  - inputData: 入力情報。
    func toVersionCandidate(_ inputData: ComposingText, options: ConvertRequestOptions) -> [Candidate] {
        let target = inputData.convertTarget

        // Trigger: "xldbg" (uncommon, no kana conversion for these letters)
        guard target == "xldbg" else { return [] }

        // Build version string with converter build identifier
        let appVersion = options.metadata?.versionString ?? "Unknown App Version"
        let converterInfo = "Converter: \(Self.converterBuildIdentifier)"
        let fullVersionString = "\(appVersion) | \(converterInfo)"

        return [
            // Full version info as first candidate (high priority)
            Candidate(
                text: fullVersionString,
                value: -5,
                composingCount: .inputCount(inputData.input.count),
                lastMid: MIDData.一般.mid,
                data: [DicdataElement(word: fullVersionString, ruby: target, cid: CIDData.固有名詞.cid, mid: MIDData.一般.mid, value: -5)],
                isLearningTarget: false
            ),
            // Converter build identifier only as second candidate
            Candidate(
                text: converterInfo,
                value: -6,
                composingCount: .inputCount(inputData.input.count),
                lastMid: MIDData.一般.mid,
                data: [DicdataElement(word: converterInfo, ruby: target, cid: CIDData.固有名詞.cid, mid: MIDData.一般.mid, value: -6)],
                isLearningTarget: false
            )
        ]
    }
}
