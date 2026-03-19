const { expect } = require("chai"); // needed for unit tests to succeed

describe("Kerdos Token", function() {
    let token;
    let owner, addr1, addr2;

    /*
    * Contract does token value conversions for mint and burn internally
    * For the other operations, we need to do a conversion using `ethers.parseEther(<enter_token_count>)`
    * as raw units are expected
    */
    beforeEach(async function() {
        // this runs before every test
        [owner, addr1, addr2] = await ethers.getSigners();
        token = await ethers.deployContract("RWASecurityToken", [
            "Kerdos", "KRDS", 1000000n
        ]);
    });

    it("Deployment should assign total supply to owner", async function() {
        // token and owner are already available here
        const ownerBalance = await token.balanceOf(owner.address);
        expect(await token.totalSupply()).to.equal(ownerBalance);
    });

    it("Mint should work to an allowlisted address", async function() {
        await token.addToAllowlist(addr1.address);
        await token.mint(addr1.address, 100n);
        expect(await token.balanceOf(addr1.address)).to.equal(ethers.parseEther("100"));
    });

    it("Mint should fail to a non-allowlisted address", async function() {
        const addr2_balance = await token.balanceOf(addr2.address);
        await expect(token.mint(addr2.address, 100n))
            .to.be.revertedWith("Token: receiver not allowlisted");        
        expect(await token.balanceOf(addr2.address)).to.equal(addr2_balance);
    });

    it("Transfer should work between allowlisted addresses", async function() {
        await token.addToAllowlist(addr1.address);
        await token.addToAllowlist(addr2.address);
        await token.mint(addr1.address, 100n);
        await token.connect(addr1).transfer(addr2.address, ethers.parseEther("10"));
        expect(await token.balanceOf(addr1.address)).to.equal(ethers.parseEther("90"));
        expect(await token.balanceOf(addr2.address)).to.equal(ethers.parseEther("10"));
    });

    it("Transfer should fail to a non-allowlisted address", async function() {
        await token.addToAllowlist(addr1.address);
        await token.mint(addr1.address, 100n);
        
        await expect(token.connect(addr1).transfer(addr2.address, ethers.parseEther("10")))
            .to.be.revertedWith("Token: receiver not allowlisted");
        
        expect(await token.balanceOf(addr1.address)).to.equal(ethers.parseEther("100"));
    });

    it("Transfer should fail if sender is blocklisted", async function() {
        await token.addToAllowlist(addr1.address);
        await token.addToAllowlist(addr2.address);
        await token.mint(addr1.address, 100n);
        await token.addToBlockedlist(addr1.address);

        await expect(token.connect(addr1).transfer(addr2.address, ethers.parseEther("10")))
            .to.be.revertedWith("Token: sender is blocked");

        expect(await token.balanceOf(addr1.address)).to.equal(ethers.parseEther("100"));
    });

    it("Burn should work", async function() {
        await token.addToAllowlist(addr1.address);
        await token.mint(addr1.address, 100n);
        await token.burn(addr1.address, 10n);
        expect(await token.balanceOf(addr1.address)).to.equal(ethers.parseEther("90"));
    });

});