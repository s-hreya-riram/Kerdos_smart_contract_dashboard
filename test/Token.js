describe("Kerdos Token", function() {
    
    // variables declared here are accessible in all tests
    let token;
    let owner, addr1, addr2;

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

    // TODO add more tests for the other functions in the Token contract

});