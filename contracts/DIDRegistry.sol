// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DIDRegistry {
    mapping(address => string) public didOf;
    event DIDRegistered(address indexed user, string did);

    function registerDID(string calldata did) external {
        didOf[msg.sender] = did;
        emit DIDRegistered(msg.sender, did);
    }
}
