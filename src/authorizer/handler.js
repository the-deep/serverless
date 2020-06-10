const jwt = require('jsonwebtoken');

const {
    JWT_SECRET_OR_PUBLIC_KEY,
} = process.env;

// TODO: Send custom message to GatewayResponse template
const UNAUTHORIZED_MESSAGE = 'Authorization Token missing or invalid';

// TODO: Policy helper function
const generatePolicy = (principalId, effect, resource) => {
  const authResponse = {};
  authResponse.principalId = principalId;
  if (effect && resource) {
    const policyDocument = {};
    policyDocument.Version = '2012-10-17';
    policyDocument.Statement = [];
    const statementOne = {};
    statementOne.Action = 'execute-api:Invoke';
    statementOne.Effect = effect;
    statementOne.Resource = resource;
    policyDocument.Statement[0] = statementOne;
    authResponse.policyDocument = policyDocument;
  }
  return authResponse;
};

// Reusable Authorizer function
module.exports.auth = (event, context, callback) => {
    if (!event.authorizationToken) {
        return callback(UNAUTHORIZED_MESSAGE);
    }

    const tokenParts = event.authorizationToken.split(' ');
    const tokenValue = tokenParts[1];

    if (!(tokenParts[0].toLowerCase() === 'bearer' && tokenValue)) {
        // no auth token!
        return callback(UNAUTHORIZED_MESSAGE);
    }
    try {
        jwt.verify(tokenValue, JWT_SECRET_OR_PUBLIC_KEY, (verifyError, decoded) => {
            if (verifyError) {
                console.log('verifyError', verifyError);
                // 401 Unauthorized
                console.log(`Token invalid. ${verifyError}`);
                return callback(UNAUTHORIZED_MESSAGE);
            }
            // is custom authorizer function
            console.log('valid from customAuthorizer', decoded);
            return callback(null, generatePolicy(decoded.sub, 'Allow', event.methodArn));
        });
    } catch (err) {
        console.log('catch error. Invalid token', err);
        return callback(UNAUTHORIZED_MESSAGE);
    }
};
