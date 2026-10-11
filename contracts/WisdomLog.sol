// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title WisdomLog
 * @dev On-Chain Wisdom Log & Care Checkpoint Registry for TIARA AI DApp on BOT Chain Mainnet
 */
contract WisdomLog {
    struct LogEntry {
        address author;
        string contentHash;
        uint256 timestamp;
        string category;
    }

    mapping(address => LogEntry[]) private patientLogs;
    address public owner;

    event LogRecorded(address indexed author, string contentHash, uint256 timestamp, string category);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can execute this");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /**
     * @dev Record a new care checkpoint or cognitive session hash on-chain
     */
    function recordWisdomLog(string memory _contentHash, string memory _category) public {
        require(bytes(_contentHash).length > 0, "Content hash cannot be empty");

        patientLogs[msg.sender].push(LogEntry({
            author: msg.sender,
            contentHash: _contentHash,
            timestamp: block.timestamp,
            category: _category
        }));

        emit LogRecorded(msg.sender, _contentHash, block.timestamp, _category);
    }

    /**
     * @dev Retrieve logs recorded by a specific address
     */
    function getLogs(address _patient) public view returns (LogEntry[] memory) {
        return patientLogs[_patient];
    }
}
