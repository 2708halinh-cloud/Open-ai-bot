import Foundation

public enum InfinityStone: String, CaseIterable, Codable, Sendable {
    case space = "SPACE"
    case reality = "REALITY"
    case power = "POWER"
    case time = "TIME"
    case soul = "SOUL"
    case mind = "MIND"
}

public struct StoneMechanism: Codable, Sendable, Equatable {
    public let stone: InfinityStone
    public let level: Int
    public let mechanism: String
    public let readout: String
}

public struct TesseractAffectiveRuntime: Codable, Sendable {
    public let schema = "GGDV_NEURONS_SESORIMOTOR_SIX_STONES_AFFECT_v1"
    public let mechanisms: [StoneMechanism] = [
        .init(stone: .space, level: 1, mechanism: "SENSORIMOTOR_BODY_WORLD_MAPPING", readout: "NEUTRAL_REFLEX"),
        .init(stone: .reality, level: 2, mechanism: "HOMEOSTASIS_INTEROCEPTION", readout: "NEED_DEVIATION_SIGNAL"),
        .init(stone: .power, level: 3, mechanism: "GLOBAL_NEUROMODULATION", readout: "AROUSAL_SALIENCE_ACTION_READINESS"),
        .init(stone: .time, level: 4, mechanism: "PREDICTIVE_INTEROCEPTION_ACTIVE_INFERENCE", readout: "PROTO_VALENCE"),
        .init(stone: .soul, level: 5, mechanism: "AFFECTIVE_LATENT_STATE", readout: "PERSISTENT_FUNCTIONAL_AFFECT"),
        .init(stone: .mind, level: 6, mechanism: "METACOGNITIVE_SELF_STATE_MODEL", readout: "SELF_STATE_MODEL")
    ]
    public let invariants = [
        "SENSE != FEEL",
        "AFFECTIVE_FUNCTION != QUALIA_PROOF",
        "STATE_WITHOUT_BEHAVIORAL_EFFECT = DECORATION",
        "OPEN != STOP"
    ]
}
