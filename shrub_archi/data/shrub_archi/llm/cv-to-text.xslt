<!-- transform.xslt -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="text" indent="no" omit-xml-declaration="yes"/>
  <xsl:template match="/">
    <CV/>
    <xsl:apply-templates select="/CV" />
    <xsl:apply-templates select="/CV/Competences/*" />
    <xsl:apply-templates select="/CV/Employments/*" />
    <xsl:apply-templates select="/CV/Categorys/*" />
  </xsl:template>
  <xsl:template match="/CV">
### Personalia<xsl:text>&#xa;</xsl:text>
*Naam*: <xsl:value-of select="./FullName"/><xsl:text>&#xa;</xsl:text>
*Nationaliteit*: <xsl:value-of select="./Nationality"/><xsl:text>&#xa;</xsl:text>
*Woonplaats*: <xsl:value-of select="./Residence"/><xsl:text>&#xa;</xsl:text>
*Waarom ik*:<xsl:text>&#xa;</xsl:text>
<xsl:value-of select="./WhyMe/Description"/>
  </xsl:template>
  <xsl:template match="/CV/Competences/Competence">
### Competentie <xsl:value-of select="./Title"/><xsl:text>&#xa;</xsl:text>
<xsl:value-of select="./Description"/>
  </xsl:template>
  <xsl:template match="/CV/Employments/Employment">
### Werkervaring als <xsl:value-of select="./Function"/><xsl:text>&#xa;</xsl:text>
*Organisatie*: <xsl:value-of select="./Organization"/><xsl:text>&#xa;</xsl:text>
<xsl:if test="./Employer">
*Employer*: <xsl:value-of select="./Employer"/><xsl:text>&#xa;</xsl:text>
</xsl:if>
*Periode*: <xsl:value-of select="./Period"/><xsl:text>&#xa;</xsl:text>
*Situatie*:
<xsl:value-of select="./Situation"/>
*Taak*:
<xsl:value-of select="./Task"/>
*Resultaat*:
<xsl:value-of select="./Result"/>
  </xsl:template>
  <xsl:template match="/CV/Categorys/Category">
### <xsl:value-of select="./Name"/><xsl:text>&#xa;</xsl:text>
    <xsl:for-each select="./Specializations/Specialization">
#### Topic: <xsl:value-of select="./Title"/><xsl:text>&#xa;</xsl:text>
*Ervaring*: <xsl:value-of select="./YearsOfExperience"/> jaren<xsl:text>&#xa;</xsl:text>
*Level*: <xsl:value-of select="./KnowledgeLevelInt" />
    </xsl:for-each>
  </xsl:template>
</xsl:stylesheet>