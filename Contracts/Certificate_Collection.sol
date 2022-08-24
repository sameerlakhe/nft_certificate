pragma solidity ^0.6.0;


import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/release-v3.0.0/contracts/token/ERC721/ERC721.sol";


contract CertificateCollection is ERC721 {
    constructor() public ERC721("CertificateToken", "CTK") {}
    struct Certificate {
        //name of the student
        string name;
        //grade of the student
        string grade;
        //description of the certificate e.g cohort name, duration of course, location etc
        string description;
        //time when the certificate is minted
        uint256 date;
        //wallet address of the minter used to sign the transaction
        string createdBy_address;
        //name of the organisation issueing the certificate
    	string minter;
        //all the above data which is encypted using an encryption key that is known only to the 
        //minter and the trusted third party issueing the encryption key
	    string encrypted_data;
    }
    
    
    mapping(uint256 => Certificate) public CertificateCollection; 


   function registerCertificate(
        address owner,
        string memory name,
        string memory grade,
        string memory description,
        string memory tokenUri,
        string memory minter,
        string memory encrypted_data
    ) public returns (uint256) {
        uint256 tokenId = totalSupply();
        _mint(owner, tokenId);
        _setTokenURI(tokenId, tokenUri);
        //string memory minter_adddress = "0xC0277d02d43Ed6105029FE6c51Fa990E696147BC";
        CertificateCollection[tokenId] = Certificate(name,
                                                    grade,
                                                    description, 
                                                    now, 
                                                    owner,
                                                    minter,
                                                    encrypted_data);
        return tokenId;
    }
}