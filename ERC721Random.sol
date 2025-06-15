// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ERC721Random {
    string public name;
    string public symbol;
    uint public _tokenIdCounter; // Simple counter for token IDs

    mapping(uint => address) private _owners;
    mapping(address => uint) private _balances;
    mapping(uint => address) private _tokenApprovals;
    mapping(address => mapping(address => bool)) private _operatorApprovals;

    event Transfer(address indexed from, address indexed to, uint indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);

    constructor(string memory _name, string memory _symbol) {
        name = _name;
        symbol = _symbol;
        _tokenIdCounter = 0; // Token IDs start from 0 or 1
    }

    // ERC721 Metadata URI (simplified) - returns empty string or placeholder
    function tokenURI(uint tokenId) public view virtual returns (string memory) {
        require(_exists(tokenId), "ERC721: URI query for nonexistent token");
        return string(abi.encodePacked("https://example.com/nft/", Strings.toString(tokenId)));
    }

    // Internal helper for toString (simplified, usually from OpenZeppelin's Strings library)
    library Strings {
        function toString(uint256 value) internal pure returns (string memory) {
            if (value == 0) {
                return "0";
            }
            uint256 temp = value;
            uint256 digits;
            while (temp != 0) {
                digits++;
                temp /= 10;
            }
            bytes memory buffer = new bytes(digits);
            while (value != 0) {
                digits -= 1;
                buffer[digits] = bytes1(uint8(48 + uint256(value % 10)));
                value /= 10;
            }
            return string(buffer);
        }
    }


    // ERC721 Basic Functions
    function balanceOf(address owner_) public view returns (uint) {
        require(owner_ != address(0), "ERC721: address zero is not a valid owner");
        return _balances[owner_];
    }

    function ownerOf(uint tokenId) public view returns (address) {
        address owner_ = _owners[tokenId];
        require(owner_ != address(0), "ERC721: owner query for nonexistent token");
        return owner_;
    }

    function approve(address to, uint tokenId) public {
        address owner_ = ownerOf(tokenId);
        require(to != owner_, "ERC721: approval to current owner");
        require(msg.sender == owner_ || isApprovedForAll(owner_, msg.sender), "ERC721: approve caller is not owner nor approved for all");
        _approve(to, tokenId);
    }

    function getApproved(uint tokenId) public view returns (address) {
        require(_exists(tokenId), "ERC721: approved query for nonexistent token");
        return _tokenApprovals[tokenId];
    }

    function setApprovalForAll(address operator, bool approved) public {
        _setApprovalForAll(msg.sender, operator, approved);
    }

    function isApprovedForAll(address owner_, address operator) public view returns (bool) {
        return _operatorApprovals[owner_][operator];
    }

    function transferFrom(address from, address to, uint tokenId) public {
        require(_isApprovedOrOwner(msg.sender, tokenId), "ERC721: transfer caller is not owner nor approved");
        _transfer(from, to, tokenId);
    }

    function safeTransferFrom(address from, address to, uint tokenId, bytes memory data) public {
        transferFrom(from, to, tokenId);
        require(_checkOnERC721Received(from, to, tokenId, data), "ERC721: transfer to non ERC721Receiver implementer");
    }

    function safeTransferFrom(address from, address to, uint tokenId) public {
        safeTransferFrom(from, to, tokenId, "");
    }


    // Internal Functions
    function _exists(uint tokenId) internal view returns (bool) {
        return _owners[tokenId] != address(0);
    }

    function _approve(address to, uint tokenId) internal {
        _tokenApprovals[tokenId] = to;
        emit Approval(ERC721Random.ownerOf(tokenId), to, tokenId);
    }

    function _setApprovalForAll(address owner_, address operator, bool approved) internal {
        require(owner_ != operator, "ERC721: approve to caller");
        _operatorApprovals[owner_][operator] = approved;
        emit ApprovalForAll(owner_, operator, approved);
    }

    function _transfer(address from, address to, uint tokenId) internal {
        require(ERC721Random.ownerOf(tokenId) == from, "ERC721: transfer from incorrect owner");
        require(to != address(0), "ERC721: transfer to the zero address");

        _approve(address(0), tokenId); // Clear approvals
        _balances[from]--;
        _balances[to]++;
        _owners[tokenId] = to;

        emit Transfer(from, to, tokenId);
    }

    // Simple Minting function (only owner can mint)
    function mint(address to) public returns (uint) {
        require(msg.sender == owner, "ERC721: Only contract owner can mint");
        _tokenIdCounter++;
        _mint(to, _tokenIdCounter);
        return _tokenIdCounter;
    }

    function _mint(address to, uint tokenId) internal {
        require(to != address(0), "ERC721: mint to the zero address");
        require(!_exists(tokenId), "ERC721: token already minted");

        _balances[to]++;
        _owners[tokenId] = to;
        emit Transfer(address(0), to, tokenId);
    }

    // Helper for ERC721Receiver (simplified, no real interface check)
    function _checkOnERC721Received(address from, address to, uint tokenId, bytes memory _data) private returns (bool) {
        if (to.code.length > 0) {
            // Simplified check: assume success for external calls
            // In a real scenario, you'd check if the receiver implements ERC721Receiver
            // using something like IERC721Receiver(to).onERC721Received
            return true;
        }
        return true;
    }

    address public owner; // Owner for minting functionality
    constructor() {
        owner = msg.sender; // The deployer becomes the owner
    }
}